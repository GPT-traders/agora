#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <memory>
#include <iostream>

#include <fstream> 
#include <csignal>
#include <cstring>
#include <sstream>
#include <string>
#include <thread>

#include "IAgoraService.h"
#include "NGIAgoraRtcConnection.h"
#include "common/file_parser/helper_h264_parser.h"
#include "common/helper.h"
#include "common/log.h"
#include "common/opt_parser.h"
#include "common/sample_common.h"
#include "common/sample_connection_observer.h"
#include "common/sample_local_user_observer.h"

#include "NGIAgoraAudioTrack.h"
#include "NGIAgoraLocalUser.h"
#include "NGIAgoraMediaNodeFactory.h"
#include "NGIAgoraMediaNode.h"


namespace py = pybind11;
using namespace agora::rtc;

class PyAgoraAPI {
public:
    PyAgoraAPI() {
        service = createAndInitAgoraService(false, true, true);
        if (!service) throw std::runtime_error("Failed to create Agora service");

        factory = service->createMediaNodeFactory();
        if (!factory) throw std::runtime_error("Failed to create media node factory");
    }

    ~PyAgoraAPI() {
        if (service) service->release();
    }

    bool connect(const std::string& appId, const std::string& channelId, const std::string& userId) {
        RtcConnectionConfiguration config;
        config.autoSubscribeAudio = false;
        config.autoSubscribeVideo = false;
        config.clientRoleType = CLIENT_ROLE_BROADCASTER;

        connection = service->createRtcConnection(config);
        if (!connection) throw std::runtime_error("Failed to create Agora connection");

        return connection->connect(appId.c_str(), channelId.c_str(), userId.c_str());
    }

    void disconnect() {
        if (connection) {
            connection->disconnect();
            connection = nullptr;
        }
    }

    void createAudioTrack() {
        audioSender = factory->createAudioPcmDataSender();
        if (!audioSender) throw std::runtime_error("Failed to create audio PCM data sender");

        customAudioTrack = service->createCustomAudioTrack(audioSender);
        if (!customAudioTrack) throw std::runtime_error("Failed to create custom audio track");

        connection->getLocalUser()->publishAudio(customAudioTrack);
    }

    void sendAudioPcmData(const py::bytes& data, int numOfSamples, int bytesPerSample, int channels, int sampleRate) {

    std::string buffer = data; // Convert py::bytes to std::string

    int sampleSize = sizeof(int16_t) * channels;
    int samplesPer10ms = sampleRate / 100;
    int sendBytes = sampleSize * samplesPer10ms;
    static int count=0;
    uint8_t frameBuf[sendBytes];

    const uint8_t* data_ptr = reinterpret_cast<const uint8_t*>(buffer.data()); // Get pointer to the data

    if (buffer.size()!=sendBytes){
        throw std::runtime_error("size mismatch");
    }else{
        std::memcpy(frameBuf, data_ptr, sendBytes);
    }
    std::cout<<"-----------------Out 1 frame--------"<<numOfSamples<<","<< agora::rtc::TWO_BYTES_PER_SAMPLE<<","<<channels<<","<<sampleRate<<std::endl;
    std::cout<<"SendBytes:"<<sendBytes<<std::endl;
    std::cout<<sizeof(frameBuf)<<std::endl;

    //----------------------------------------

//     //------------------------------------------------

//   std::ostringstream filename;
//   filename << "py_out_" << count << ".bin";

//   // Open a binary file for writing
//   std::ofstream outFile(filename.str(), std::ios::binary);
//   if (!outFile.is_open()) {
//       std::cerr << "Failed to open file for writing." << std::endl;
//       return ;
//   }

//   // Write the buffer to the file
//   outFile.write(reinterpret_cast<const char*>(frameBuf), sizeof(frameBuf));

//   // Close the file
//   outFile.close();

//   // Increment the file count after writing
//   count++;



//   //-----------------------------------------------



    //-----------------------------------------
    if (audioSender->sendAudioPcmData(frameBuf, 0, 0, numOfSamples,  agora::rtc::TWO_BYTES_PER_SAMPLE, channels, sampleRate) < 0) {
        throw std::runtime_error("Failed to send audio PCM data");
    }
}

private:
    agora::base::IAgoraService* service = nullptr;
    agora::agora_refptr<agora::rtc::IRtcConnection> connection = nullptr;
    agora::agora_refptr<agora::rtc::IMediaNodeFactory> factory = nullptr;
    agora::agora_refptr<agora::rtc::IAudioPcmDataSender> audioSender = nullptr;
    agora::agora_refptr<agora::rtc::ILocalAudioTrack> customAudioTrack = nullptr;
};

PYBIND11_MODULE(pyagora, m) {
    py::class_<PyAgoraAPI>(m, "AgoraAPI")
        .def(py::init<>())
        .def("connect", &PyAgoraAPI::connect)
        .def("disconnect", &PyAgoraAPI::disconnect)
        .def("create_audio_track", &PyAgoraAPI::createAudioTrack)
        .def("send_audio_pcm_data", &PyAgoraAPI::sendAudioPcmData);
}
