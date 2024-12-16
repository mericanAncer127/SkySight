// src/utils/downloadUtils.ts
export const downloadImage = async (url: string, filename: string) => {
  try {
    const response = await fetch(url, {
      mode: 'cors', // Ensure CORS is handled
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    console.error('Error downloading the image:', error);
    alert('Failed to download image. Please try again.');
  }
};
