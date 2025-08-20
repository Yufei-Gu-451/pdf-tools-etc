import argparse
import fitz  # PyMuPDF library
from pathlib import Path
import sys
import os

def convert_pdf_to_numbered_images(pdf_path_str: str, dpi: int):
    """
    Converts a single PDF file's pages to numbered PNG images, saving them
    in a new folder in the user's home directory.

    Args:
        pdf_path_str (str): The path to the PDF file to convert.
    """
    pdf_path = Path(pdf_path_str)

    # --- 1. Validate the input file ---
    if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
        print(f"❌ Error: The path '{pdf_path}' is not a valid PDF file.")
        sys.exit(1)

    # --- 2. Create the output directory in the upper folder ---
    output_dir = os.path.dirname(pdf_path)
    output_dir = os.path.join(output_dir, f"{pdf_path.stem}_images")
    os.makedirs(output_dir, exist_ok=True)

    print(f"✅ Input PDF: '{pdf_path.name}'")
    print(f"📂 Output will be saved in: {output_dir}")

    # --- 3. Process the PDF ---
    try:
        # Open the PDF using a context manager for safety
        with fitz.open(pdf_path) as doc:
            page_count = doc.page_count
            if page_count == 0:
                print("⚠️ The PDF appears to be empty.")
                return

            # Determine the zero-padding needed for filenames (e.g., 01, 02... or 001, 002...)
            # This ensures files sort correctly in your file explorer.
            zfill_width = len(str(page_count))

            print(f"📄 Converting {page_count} pages...")

            # --- 4. Iterate and save pages as numbered images ---
            for i in range(page_count):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi)  # Render page to an image object

                # Name images sequentially (e.g., 01.png, 02.png, ...)
                image_name = f"{str(i + 1).zfill(zfill_width)}.png"
                output_file_path = os.path.join(output_dir, image_name)
                pix.save(output_file_path)

            print(f"\n🎉 Conversion complete! All {page_count} pages saved.")

    except Exception as e:
        print(f"❗️ An error occurred while processing the PDF: {e}")
        sys.exit(1)


def main():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Converts a PDF's pages into numbered images in a folder in your home directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--pdf_file",
        type=str,
        help="The full path to the PDF file you want to convert."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=400,
        help="輸出影像的 DPI (每英吋點數)。預設為 300。"
    )
    args = parser.parse_args()
    convert_pdf_to_numbered_images(args.pdf_file, args.dpi)


if __name__ == "__main__":
    main()