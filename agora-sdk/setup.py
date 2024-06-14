from distutils.core import setup, Extension

agora_module = Extension('agora_interface',
                         sources=['agora_interface.i', './agora_rtc_sdk/example/h264_pcm/sample_send_h264_pcm.cpp'],#,'./agora_rtc_sdk/example/h264_pcm/sample_receive_h264_pcm.cpp'],
                         include_dirs=[
                             './agora_rtc_sdk/agora_sdk/include/',
                             './agora_rtc_sdk/example/',
                             './agora_rtc_sdk/example/common/'
                         ],
                         extra_compile_args=["-std=c++11"])  # Adjust compile args as necessary

setup(name='agora_interface',
      version='0.1',
      author='AII',
      description="""A Python wrapper for custom Agora SDK functionalities""",
      ext_modules=[agora_module])
