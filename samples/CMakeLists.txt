cmake_minimum_required ( VERSION 3.20 )

project ( grab VERSION 0.1.0 LANGUAGES CXX )

set ( CMAKE_FIND_DEBUG_MODE OFF )

set ( CMAKE_C_STANDARD 17 )
set ( CMAKE_C_STANDARD_REQUIRED ON )

set ( CMAKE_CXX_STANDARD 23 )
set ( CMAKE_CXX_STANDARD_REQUIRED ON )

# Set the CMAKE_PREFIX_PATH to include the Pylon SDK directory
set ( CMAKE_PREFIX_PATH "C:/Program Files/Basler/pylon 8/Development/CMake/" ${CMAKE_PREFIX_PATH} )
list( APPEND CMAKE_PREFIX_PATH $ENV{PYLON_DEV_DIR} )

# Find the Pylon package
find_package ( pylon REQUIRED )

add_executable ( grab "grab.cpp" )

target_link_libraries ( grab pylon::pylon )
