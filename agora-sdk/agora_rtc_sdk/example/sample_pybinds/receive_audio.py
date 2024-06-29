import pyagora_receive as pyagora
import time
options = pyagora.SampleOptions()
options.appId = "007eJxTYNi0l1uNadWypalv5fNKw76oK7fdd208eHxysoj1tBaVpL0KDBapZskWJompKZaJBiYGiWmWaYkpKckGFpbmpqbmJimpxRfL0hoCGRkKhXyZGBkgEMTnYUhJzc2PT85IzMtLzWFgAAAs9SH6"
options.channelId = "demo_channel"
# options.userId = "YOUR_USER_ID"
# options.remoteUserId = "REMOTE_USER_ID"
options.audioFile = "output_audio.pcm"
options.audio.sampleRate = 16000
options.audio.numOfChannels = 1

agora = pyagora.PyAgora(options)

if agora.connect():
    try:
        print("Connected to Agora channel. Receiving audio data...")
        agora.run()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        agora.disconnect()
else:
    print("Failed to connect to Agora channel.")
