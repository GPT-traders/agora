import agora_interface

# Example of using the module
client = agora_interface("76ae593c16f04b8b940ab1ef068ff5c4", "aii_channel")
client.connect()
client.send_audio_frame("./agora_rtc_sdk/example/out/test_data/send_video.h264")
client.send_video_frame("./agora_rtc_sdk/example/out/test_data/send_audio_16k_1ch.pcm")
client.disconnect()