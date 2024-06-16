cmake_minimum_required(VERSION 2.4)
project(DefaultSamples)

# Common file parsers
file(GLOB FILE_PARSER_CPP_FILES
     "${PROJECT_SOURCE_DIR}/../common/file_parser/helper_h264_parser.cpp")


# Add pybind11
add_subdirectory("${PROJECT_SOURCE_DIR}/../extern/pybind11" ${CMAKE_CURRENT_BINARY_DIR}/pybind11_build)

# Define common source files
set(COMMON_SOURCE_DIR "${PROJECT_SOURCE_DIR}/../common")
file(GLOB COMMON_CPP_FILES
     "${COMMON_SOURCE_DIR}/*.cpp"
     "${COMMON_SOURCE_DIR}/file_parser/helper_h264_parser.cpp")


# Pybind11 module (add this for the Python binding)
pybind11_add_module(pyagora "${PROJECT_SOURCE_DIR}/pybind_audio.cpp" ${COMMON_CPP_FILES})
