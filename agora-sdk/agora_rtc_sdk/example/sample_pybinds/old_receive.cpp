#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <iostream>
#include <fstream>
#include <memory>
#include <cstring>
#include <cstdint> 

#include "IAgoraService.h"
#include "NGIAgoraRtcConnection.h"
#include "common/log.h"
#include "common/sample_common.h"
#include <iostream>

#include <csignal>
#include <cstring>
#include <sstream>
#include <string>
#include <thread>
#include <unistd.h>

#include "IAgoraService.h"
#include "NGIAgoraRtcConnection.h"
#include "common/opt_parser.h"
#include "common/sample_local_user_observer.h"

#include "NGIAgoraAudioTrack.h"
#include "NGIAgoraLocalUser.h"
#include "NGIAgoraMediaNodeFactory.h"
#include "NGIAgoraMediaNode.h"
#include "NGIAgoraVideoTrack.h"
#define DEFAULT_FILE_LIMIT (100 * 1024 * 1024)

namespace py = pybind11;
using namespace agora::rtc;
using namespace agora::base;
using namespace agora::media;
using namespace std;

class PcmFrameObserver : public agora::media::IAudioFrameObserverBase {
 public:
  PcmFrameObserver(const std::string& outputFilePath)
      : outputFilePath_(outputFilePath),
        pcmFile_(nullptr),
        fileCount(0),
        fileSize_(0) {}

  bool onPlaybackAudioFrame(const char* channelId,AudioFrame& audioFrame) override { return true; };

  bool onRecordAudioFrame(const char* channelId,AudioFrame& audioFrame) override { return true; };

  bool onMixedAudioFrame(const char* channelId,AudioFrame& audioFrame) override { return true; };

  bool onPlaybackAudioFrameBeforeMixing(const char* channelId, agora::media::base::user_id_t userId, AudioFrame& audioFrame) override{
  // Create new file to save received PCM samples

  std::cout<<"audio is received"<<std::endl;
  
  if (!pcmFile_) {
    std::string fileName = (++fileCount > 1)
                               ? (outputFilePath_ + std::to_string(fileCount))
                               : outputFilePath_;

    if (!(pcmFile_ = fopen(fileName.c_str(), "w"))) {
      AG_LOG(ERROR, "Failed to create received audio file %s",
             fileName.c_str());
      return false;
    }
    AG_LOG(INFO, "Created file %s to save received PCM samples",
           fileName.c_str());
  }

  // Write PCM samples
  size_t writeBytes =
      audioFrame.samplesPerChannel * audioFrame.channels * sizeof(int16_t);
  if (fwrite(audioFrame.buffer, 1, writeBytes, pcmFile_) != writeBytes) {
    AG_LOG(ERROR, "Error writing decoded audio data: %s", std::strerror(errno));
    return false;
  }
  fileSize_ += writeBytes;

  // Close the file if size limit is reached
  if (fileSize_ >= DEFAULT_FILE_LIMIT) {
    fclose(pcmFile_);
    pcmFile_ = nullptr;
    fileSize_ = 0;
  }
  return true;
}; 

  int getObservedAudioFramePosition() override {return 0;};

  bool onEarMonitoringAudioFrame(AudioFrame& audioFrame) override {return true;};

  AudioParams getEarMonitoringAudioParams()override {return  AudioParams();};

  AudioParams getPlaybackAudioParams() override {return  AudioParams();};

  AudioParams getRecordAudioParams()  override {return  AudioParams();};

  AudioParams getMixedAudioParams() override {return  AudioParams();};


 private:
  std::string outputFilePath_;
  FILE* pcmFile_;
  int fileCount;
  int fileSize_;
};


class PyAgoraConnection {
public:
    PyAgoraConnection(const std::string& appId, const std::string& channelId, const std::string& userId) {
        service = createAndInitAgoraService(false, true, true);
        if (!service) throw std::runtime_error("Failed to create Agora service");

        agora::rtc::RtcConnectionConfiguration config;
        config.clientRoleType = CLIENT_ROLE_AUDIENCE;  // or CLIENT_ROLE_BROADCASTER based on your need
        config.autoSubscribeAudio = false;
        config.autoSubscribeVideo = false;
        config.enableAudioRecordingOrPlayout =
            false;
        connection = service->createRtcConnection(config);
        if (!connection) throw std::runtime_error("Failed to create Agora connection");

        if (connection->connect(appId.c_str(), channelId.c_str(), userId.c_str())) {
            throw std::runtime_error("Failed to connect to channel");
        }

        
    }

    void connectionReceiver(){
        std::cout<<"Connection receiver started"<<std::endl;
        connection->getLocalUser()->subscribeAllAudio();
        auto localUserObserver =
      std::make_shared<SampleLocalUserObserver>(connection->getLocalUser());
      auto pcmFrameObserver = std::make_shared<PcmFrameObserver>("received_audio_sample.pcm");
  if (connection->getLocalUser()->setPlaybackAudioFrameBeforeMixingParameters(
        //   options.audio.numOfChannels, options.audio.sampleRate)) {
        1, 16000)) {
    AG_LOG(ERROR, "Failed to set audio frame parameters!");
    return ;
  }
  localUserObserver->setAudioFrameObserver(pcmFrameObserver.get());
    }

    

    void disconnect() {
        if (connection) {
            connection->disconnect();
            connection = nullptr;
        }
        if (service) {
            service->release();
            service = nullptr;
        }
    }
    ~PyAgoraConnection() {
        if (connection) {
            connection->disconnect();
            connection = nullptr;
        }
        if (service) {
            service->release();
            service = nullptr;
        }
    }

private:
    agora::base::IAgoraService* service = nullptr;
    agora::agora_refptr<agora::rtc::IRtcConnection> connection = nullptr;
};

PYBIND11_MODULE(pyagora_receive, m) {
    // py::class_<PyAgoraConnection>(m, "AgoraConnection")
    //     .def(py::init<const std::string&, const std::string&, const std::string&>())
    //     .def("receiver_setup", &PyAgoraConnection::connectionReceiver)
    //     .def("disconnect", &PyAgoraConnection::disconnect);

    py::class_<PyAgoraConnection>(m, "AgoraConnection")
        .def(py::init<const std::string&, const std::string&, const std::string&>())
        .def("setup_audio_receivers", &PyAgoraConnection::connectionReceiver)
        .def("disconnect", &PyAgoraConnection::disconnect);
    // py::class_<PcmFrameObserver, IAudioFrameObserverBase>(m, "PcmFrameObserver")
    //     .def(py::init<const std::string&>())
    //     .def("on_playback_audio_frame_before_mixing", &PyPcmFrameObserver::onPlaybackAudioFrameBeforeMixing);
}
