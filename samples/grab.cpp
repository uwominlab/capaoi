// clang-format off
/*****************************************************************//**
 * \file   grab.cpp
 * \brief  This sample illustrates how to grab and process images using the CInstantCamera class.
 * The images are grabbed and processed asynchronously, i.e.,
 * while the application is processing a buffer, the acquisition of the next buffer is done
 * in parallel.
 * 
 * The CInstantCamera class uses a pool of buffers to retrieve image data
 * from the camera device. Once a buffer is filled and ready,
 * the buffer can be retrieved from the camera object for processing. The buffer
 * and additional image data are collected in a grab result. The grab result is
 * held by a smart pointer after retrieval. The buffer is automatically reused
 * when explicitly released or when the smart pointer object is destroyed.
 * 
 * \author Xuhua Huang <xhuan484@uwo.ca>
 * \date   January 2025
 *********************************************************************/
// clang-format on

// Include files to use the pylon API.
#include <pylon/PylonIncludes.h>

#ifdef PYLON_WIN_BUILD
#include <pylon/PylonGUI.h>
#endif

// Number of images to be grabbed.
static inline const uint32_t c_countOfImagesToGrab = 100;

int main(int /*argc*/, char* /*argv*/[]) {
    // The exit code of the sample application.
    int exitCode = 0;

    // Namespace for using pylon objects.
    // using namespace Pylon;
    using Pylon::PylonInitialize;
    using Pylon::PylonTerminate;

    // Before using any pylon methods, the pylon runtime must be initialized.
    PylonInitialize();

    try {
        // Create an instant camera object with the camera device found first.
        using Pylon::CInstantCamera;
        using Pylon::CTlFactory;
        CInstantCamera camera{CTlFactory::GetInstance().CreateFirstDevice()};

        // Print the model name of the camera.
        std::cout << "Using device " << camera.GetDeviceInfo().GetModelName() << "\n";

        // The parameter MaxNumBuffer can be used to control the count of buffers
        // allocated for grabbing. The default value of this parameter is 10.
        camera.MaxNumBuffer = 5;

        // Start the grabbing of c_countOfImagesToGrab images.
        // The camera device is parameterized with a default configuration which
        // sets up free-running continuous acquisition.
        camera.StartGrabbing(c_countOfImagesToGrab);

        // This smart pointer will receive the grab result data.
        using Pylon::CGrabResultPtr;
        using Pylon::TimeoutHandling_ThrowException;
        CGrabResultPtr ptrGrabResult;

        // Camera.StopGrabbing() is called automatically by the RetrieveResult() method
        // when c_countOfImagesToGrab images have been retrieved.
        while (camera.IsGrabbing()) {
            // Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            camera.RetrieveResult(5000, ptrGrabResult, TimeoutHandling_ThrowException);

            // Image grabbed successfully?
            if (ptrGrabResult->GrabSucceeded()) {
                // Access the image data.
                std::cout << "SizeX: " << ptrGrabResult->GetWidth() << "\n";
                std::cout << "SizeY: " << ptrGrabResult->GetHeight() << "\n";
                const uint8_t* pImageBuffer = (uint8_t*)ptrGrabResult->GetBuffer();
                std::cout << "Gray value of first pixel: " << (uint32_t)pImageBuffer[0] << "\n" << "\n";

#ifdef PYLON_WIN_BUILD
                // Display the grabbed image.
                Pylon::DisplayImage(1, ptrGrabResult);
#endif
            } else {
                std::cout << "Error: " << std::hex << ptrGrabResult->GetErrorCode() << std::dec << " "
                          << ptrGrabResult->GetErrorDescription() << "\n";
            }
        }
    } catch (const GENICAM_NAMESPACE::GenericException& e) {
        // Error handling.
        std::cerr << "An exception occurred." << "\n" << e.GetDescription() << "\n";
        exitCode = 1;
    }

    // Comment the following two lines to disable waiting on exit.
    std::cerr << "\n" << "Press enter to exit." << "\n";
    while (std::cin.get() != '\n')
        ;

    // Releases all pylon resources.
    PylonTerminate();

    return exitCode;
}
