"use client";
import { useState, ChangeEvent } from "react";

export default function Home() {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [translatedImages, setTranslatedImages] = useState<string[]>([]);
  const [targetLang, setTargetLang] = useState<string>("vi"); // Default target language is Spanish

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

  return (
    <div>
      <h1>Translate Text in Image with Next.js and Flask</h1>
      <div>
        <label htmlFor="targetLang">Select Target Language: </label>
        <select
          id="targetLang"
          value={targetLang}
          onChange={(e) => setTargetLang(e.target.value)}
          className="text-black"
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
      />
      <div style={{ display: "flex", flexWrap: "wrap", gap: "20px" }}>
        {selectedImages.map((image, index) => (
          <div
            key={index}
            style={{ textAlign: "center" }}
            className="flex flex-row pl-8 pr-8 justify-around items-center w-full"
          >
            <img
              src={URL.createObjectURL(image)}
              alt={`Selected ${index}`}
              style={{ maxWidth: "500px", marginTop: "20px" }}
            />
            {translatedImages[index] && (
              <img
                src={translatedImages[index]}
                alt={`Translated ${index}`}
                style={{ maxWidth: "500px", marginTop: "20px" }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
