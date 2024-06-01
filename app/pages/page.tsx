"use client";
import { useState, ChangeEvent } from "react";

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [translatedImage, setTranslatedImage] = useState<string | null>(null);
  const [targetLang, setTargetLang] = useState<string>("es"); // Default target language is Spanish

  const handleImageUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);

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
      setTranslatedImage(base64Image);
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
        >
          <option value="vi">Vietnam</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="zh-cn">Chinese (Simplified)</option>
          {/* Add more languages as needed */}
        </select>
      </div>
      <input type="file" accept="image/*" onChange={handleImageUpload} />
      {selectedImage && (
        <img
          src={URL.createObjectURL(selectedImage)}
          alt="Selected"
          style={{ maxWidth: "500px", marginTop: "20px" }}
        />
      )}
      {translatedImage && (
        <img
          src={translatedImage}
          alt="Translated"
          style={{ maxWidth: "500px", marginTop: "20px" }}
        />
      )}
    </div>
  );
}
