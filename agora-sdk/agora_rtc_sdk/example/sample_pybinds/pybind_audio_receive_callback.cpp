#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <csignal>
#include <cstring>
#include <sstream>
#include <string>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <unistd.h>

#include "IAgoraService.h"
#include "NGIAgoraRtcConnection.h"
#include "common/log.h"
#include "common/opt_parser.h"
#include "common/sample_common.h"
#include "common/sample_local_user_observer.h"
#include "NGIAgoraAudioTrack.h"
#include "NGIAgoraLocalUser.h"
#include "NGIAgoraMediaNodeFactory.h"
#include "NGIAgoraMediaNode.h"
#include "NGIAgoraVideoTrack.h"

#define DEFAULT_SAMPLE_RATE (16000)
#define DEFAULT_NUM_OF_CHANNELS (1)
#define DEFAULT_AUDIO_FILE "received_audio.pcm"
#define DEFAULT_FILE_LIMIT (100 * 1024 * 1024)
#define STREAM_TYPE_HIGH "high"
#define STREAM_TYPE_LOW "low"

namespace py = pybind11;

struct SampleOptions {
  std::string appId;
  std::string channelId;
  std::string userId;
  std::string remoteUserId;
  std::string streamType = STREAM_TYPE_HIGH;
  std::string audioFile = DEFAULT_AUDIO_FILE;

  struct Audio {
    int sampleRate = DEFAULT_SAMPLE_RATE;
    int numOfChannels = DEFAULT_NUM_OF_CHANNELS;
  } audio;
};

class PcmFrameObserver : public agora::media::IAudioFrameObserverBase {
 public:
 std::queue<std::vector<uint8_t>> audioQueue_;
  PcmFrameObserver(const std::string& outputFilePath)
      : outputFilePath_(outputFilePath), pcmFile_(nullptr), fileCount(0), fileSize_(0) {}


  bool isQueueEmpty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return audioQueue_.empty();
    }

    size_t queueSize() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return audioQueue_.size();
    }


  virtual bool onPlaybackAudioFrame(const char* channelId, AudioFrame& audioFrame) override {
      return true;
  }

  virtual bool onRecordAudioFrame(const char* channelId, AudioFrame& audioFrame) override {
      return true;
  }

  virtual bool onMixedAudioFrame(const char* channelId, AudioFrame& audioFrame) override {
      return true;
  }

  int getObservedAudioFramePosition() override {return 0;};

  virtual AudioParams getPlaybackAudioParams() override {
      return AudioParams();
  }

  virtual AudioParams getRecordAudioParams() override {
      return AudioParams();
  }

  virtual AudioParams getMixedAudioParams() override {
      return AudioParams();
  }

  virtual AudioParams getEarMonitoringAudioParams() override {
      return AudioParams();
  }

  virtual bool onEarMonitoringAudioFrame(AudioFrame& audioFrame) override {
      return true;
  }

  bool onPlaybackAudioFrameBeforeMixing(const char* channelId, agora::media::base::user_id_t userId, AudioFrame& audioFrame) override {
    if (!pcmFile_) {
        std::string fileName = (++fileCount > 1) ? (outputFilePath_ + std::to_string(fileCount)) : outputFilePath_;
        if (!(pcmFile_ = fopen(fileName.c_str(), "wb"))) {
            AG_LOG(ERROR, "Failed to create received audio file %s", fileName.c_str());
            return false;
        }
        AG_LOG(INFO, "Created file %s to save received PCM samples", fileName.c_str());
    }

    size_t writeBytes = audioFrame.samplesPerChannel * audioFrame.channels * sizeof(int16_t);
    if (fwrite(audioFrame.buffer, 1, writeBytes, pcmFile_) != writeBytes) {
        AG_LOG(ERROR, "Error writing decoded audio data: %s", std::strerror(errno));
        return false;
    }
    fileSize_ += writeBytes;

    if (fileSize_ >= DEFAULT_FILE_LIMIT) {
        fclose(pcmFile_);
        pcmFile_ = nullptr;
        fileSize_ = 0;
    }

    // Correcting the buffer handling:
    const uint8_t* dataStart = static_cast<const uint8_t*>(audioFrame.buffer);
    std::vector<uint8_t> buffer(dataStart, dataStart + writeBytes);

    {
        std::lock_guard<std::mutex> lock(mutex_);
        audioQueue_.push(std::move(buffer));
        cv_.notify_one();
    }

    return true;
}


  std::vector<uint8_t> popAudioData() {
    std::unique_lock<std::mutex> lock(mutex_);
    cv_.wait(lock, [&] { return !audioQueue_.empty(); });
    auto data = std::move(audioQueue_.front());
    audioQueue_.pop();
    return data;
  }

 private:
  std::string outputFilePath_;
  FILE* pcmFile_;
  int fileCount;
  int fileSize_;
  // std::queue<std::vector<uint8_t>> audioQueue_;
  mutable std::mutex mutex_;
  std::condition_variable cv_;
};

class PyAgora {
public:
  std::shared_ptr<PcmFrameObserver> pcmFrameObserver_;
  PyAgora(const SampleOptions& options) : options_(options){
    std::signal(SIGQUIT, SignalHandler);
    std::signal(SIGABRT, SignalHandler);
    std::signal(SIGINT, SignalHandler);
  }

  ~PyAgora() {
    disconnect();
  }

  bool connect() {
    service_ = createAndInitAgoraService(false, true, true);
    if (!service_) {
      AG_LOG(ERROR, "Failed to create Agora service!");
      return false;
    }

    agora::rtc::RtcConnectionConfiguration ccfg;
    ccfg.clientRoleType = agora::rtc::CLIENT_ROLE_AUDIENCE;
    ccfg.autoSubscribeAudio = false;
    ccfg.autoSubscribeVideo = false;
    ccfg.enableAudioRecordingOrPlayout = false;

    connection_ = service_->createRtcConnection(ccfg);
    if (!connection_) {
      AG_LOG(ERROR, "Failed to create Agora connection!");
      return false;
    }
    connection_->getLocalUser()->subscribeAllAudio();
    if (connection_->connect(options_.appId.c_str(), options_.channelId.c_str(), options_.userId.c_str())) {
      AG_LOG(ERROR, "Failed to connect to Agora channel!");
      return false;
    }

    localUserObserver_ = std::make_shared<SampleLocalUserObserver>(connection_->getLocalUser());
    pcmFrameObserver_ = std::make_shared<PcmFrameObserver>(options_.audioFile);
    if (connection_->getLocalUser()->setPlaybackAudioFrameBeforeMixingParameters(options_.audio.numOfChannels, options_.audio.sampleRate)) {
      AG_LOG(ERROR, "Failed to set audio frame parameters! Sample rate: %d, Channels: %d", options_.audio.sampleRate, options_.audio.numOfChannels);
      return false;
    }
    localUserObserver_->setAudioFrameObserver(pcmFrameObserver_.get());

    AG_LOG(INFO, "Connected and started receiving audio & video data...");
    return true;
  }

  void disconnect() {
    if (connection_) {
      localUserObserver_->unsetAudioFrameObserver();
      if (connection_->disconnect()) {
        AG_LOG(ERROR, "Failed to disconnect from Agora channel!");
      }
      AG_LOG(INFO, "Disconnected from Agora channel successfully");
      connection_ = nullptr;
    }

    if (service_) {
      service_->release();
      service_ = nullptr;
    }
  }

  void run() {
    while (!exitFlag_) {
      usleep(10000);
    }
  }

  static void SignalHandler(int sigNo) { exitFlag_ = true; }

private:
  SampleOptions options_;
  agora::base::IAgoraService* service_ = nullptr;
  agora::agora_refptr<agora::rtc::IRtcConnection> connection_;
  std::shared_ptr<SampleLocalUserObserver> localUserObserver_;
  // std::shared_ptr<PcmFrameObserver> pcmFrameObserver_;
  static bool exitFlag_;
};

bool PyAgora::exitFlag_ = false;

PYBIND11_MODULE(pyagora_receive_callback, m) {
    py::class_<SampleOptions>(m, "SampleOptions")
        .def(py::init<>())
        .def_readwrite("appId", &SampleOptions::appId)
        .def_readwrite("channelId", &SampleOptions::channelId)
        .def_readwrite("userId", &SampleOptions::userId)
        .def_readwrite("remoteUserId", &SampleOptions::remoteUserId)
        .def_readwrite("streamType", &SampleOptions::streamType)
        .def_readwrite("audioFile", &SampleOptions::audioFile)
        .def_readwrite("audio", &SampleOptions::audio);

    py::class_<SampleOptions::Audio>(m, "Audio")
        .def(py::init<>())
        .def_readwrite("sampleRate", &SampleOptions::Audio::sampleRate)
        .def_readwrite("numOfChannels", &SampleOptions::Audio::numOfChannels);

    py::class_<PcmFrameObserver, std::shared_ptr<PcmFrameObserver>>(m, "PcmFrameObserver")
    .def(py::init<const std::string&>())
    .def("pop_audio_data", &PcmFrameObserver::popAudioData)
    .def("is_queue_empty", &PcmFrameObserver::isQueueEmpty)
    .def("queue_size", &PcmFrameObserver::queueSize);

    py::class_<PyAgora>(m, "PyAgora")
        .def(py::init<const SampleOptions&>())
        .def("connect", &PyAgora::connect)
        .def("disconnect", &PyAgora::disconnect)
        .def("run", &PyAgora::run)
        .def_property("pcm_frame_observer", [](PyAgora &self) { return self.pcmFrameObserver_; }, nullptr);
}
