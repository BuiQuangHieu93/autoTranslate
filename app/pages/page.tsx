"use client";
import { useState, ChangeEvent } from "react";
import JSZip from "jszip";
import { saveAs } from "file-saver";

export default function Home() {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [translatedImages, setTranslatedImages] = useState<string[]>([]);
  const [targetLang, setTargetLang] = useState<string>("vi"); // Default target language is Vietnamese

  const handleImageUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const fileArray = Array.from(files);
      setSelectedImages(fileArray);

      const translatedImagePromises = fileArray.map(async (file) => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("target_lang", targetLang);

        const response = await fetch(
          "http://localhost:5000/translate_and_replace",
          {
            method: "POST",
            body: formData,
          }
        );

        const data = await response.json();
        const hexImage = data.image;
        const base64Image = `data:image/png;base64,${Buffer.from(
          hexImage,
          "hex"
        ).toString("base64")}`;
        return base64Image;
      });

      const translatedImageArray = await Promise.all(translatedImagePromises);
      setTranslatedImages(translatedImageArray);
    }
  };

  const handleDownload = (base64Image: string, index: number) => {
    const link = document.createElement("a");
    link.href = base64Image;
    link.download = `translated_image_${index + 1}.png`;
    link.click();
  };

  const handleDownloadAll = () => {
    const zip = new JSZip();
    translatedImages.forEach((base64Image, index) => {
      const imgData = base64Image.split(",")[1];
      zip.file(`translated_image_${index + 1}.png`, imgData, { base64: true });
    });

    zip.generateAsync({ type: "blob" }).then((content) => {
      saveAs(content, "translated_images.zip");
    });
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4 w-full flex justify-center">
        Translate Text in Image with Next.js and Flask
      </h1>
      <div className="mb-4 flex items-center gap-4">
        <label
          htmlFor="targetLang"
          className="text-lg font-medium text-gray-700"
        >
          Select Target Language:
        </label>
        <select
          id="targetLang"
          value={targetLang}
          onChange={(e) => setTargetLang(e.target.value)}
          className="mt-1 block w-full sm:w-auto pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md text-black font-normal"
        >
          <option value="vi">Vietnamese</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="zh-cn">Chinese (Simplified)</option>
          {/* Add more languages as needed */}
        </select>
      </div>

      <input
        type="file"
        accept="image/*"
        multiple
        onChange={handleImageUpload}
        className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
      />
      <div className="flex gap-4 mt-4 flex-wrap">
        {selectedImages.map((image, index) => (
          <div
            key={index}
            className="text-center flex flex-row justify-around w-full flex-wrap"
          >
            <img
              src={URL.createObjectURL(image)}
              alt={`Selected ${index}`}
              className="mt-4 h-screen"
            />
            <div className="flex flex-row">
              {translatedImages[index] && (
                <>
                  <img
                    src={translatedImages[index]}
                    alt={`Translated ${index}`}
                    className="h-screen mt-4"
                  />
                  <button
                    onClick={() =>
                      handleDownload(translatedImages[index], index)
                    }
                    className="block mt-2 px-4 py-2 bg-green-500 text-white rounded-lg w-64 h-10 rotate-90 -translate-x-28 translate-y-28 "
                  >
                    Download Translated Image
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
      {translatedImages.length > 0 && (
        <button
          onClick={handleDownloadAll}
          className="block mt-4 px-4 py-2 bg-green-500 text-white rounded-lg w-full justify-center"
        >
          Download All Translated Images
        </button>
      )}
    </div>
  );
}
