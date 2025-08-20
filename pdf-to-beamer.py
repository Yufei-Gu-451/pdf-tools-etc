import os
import base64
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from dotenv import load_dotenv
from openai import OpenAI
import re

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_pdf_content(pdf_path, images_dir="images"):
    """Extract text with positions and images from PDF"""
    doc = fitz.open(pdf_path)
    content = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_blocks = page.get_text("blocks")
        images = page.get_images()

        # Extract and save images
        img_paths = []
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]
            img_name = f"page_{page_num + 1}_image_{img_index}.{img_ext}"
            img_path = os.path.join(images_dir, img_name)

            with open(img_path, "wb") as f:
                f.write(img_bytes)
            img_paths.append(img_path)

        # Store text blocks with normalized coordinates
        text_elements = []
        for block in text_blocks:
            x0, y0, x1, y1, text, _, _ = block
            text_elements.append({
                "text": text.strip(),
                "x": x0 / page.rect.width,
                "y": 1 - y1 / page.rect.height,  # Flip Y-axis
                "width": (x1 - x0) / page.rect.width
            })

        content.append({
            "page_num": page_num,
            "text": text_elements,
            "images": img_paths,
            "dimensions": (page.rect.width, page.rect.height)
        })

    return content


def convert_page_to_image(pdf_path, page_num, output_dir="temp"):
    """Convert PDF page to image and return base64 string"""
    images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_path = os.path.join(output_dir, f"page_{page_num + 1}.jpg")
    images[0].save(image_path, "JPEG")

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_beamer_frame(page_data, base64_image):
    """Generate LaTeX Beamer code using OpenAI API"""
    system_prompt = """You are a LaTeX expert. Convert this slide to OverLeaf Beamer.
    Use this template:

    \begin{frame}
    \frametitle{Summary}
    % Add bullet points using 
        \begin{enumerate}
        \item TBD
        \end{enumerate}
    % Add images using \includegraphics
    \end{frame}

    Remove the page number.
    Return ONLY the LaTeX code, no explanations."""

    user_prompt = f"""Slide content:
    Text elements: {page_data['text']}
    Images: {page_data['images']}
    Page dimensions: {page_data['dimensions']}"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0.1
    )

    return response.choices[0].message.content


def create_latex_document(frame, output_file="presentation.tex"):
    """Create complete LaTeX document from frames"""
    preamble = """\\documentclass{beamer}
    \\usepackage{textpos}
    \\usepackage{graphicx}
    \\begin{document}
    """
    postamble = "\\end{document}"

    with open(output_file, "w", encoding="utf-8", errors="replace") as f:
        # f.write(preamble)
        # Clean up any markdown formatting
        clean_frame = re.sub(r"```latex", "", str(frame))
        clean_frame = re.sub(r"```", "", clean_frame)
        f.write(clean_frame + "\n")
        # f.write(postamble)


def concat_beamer_files(output_dir="beamers", output_file="beamer.tex"):
    """Concatenate all Beamer files into a single LaTeX document"""
    preamble = """\\documentclass{beamer}
    \\usepackage{textpos}
    \\usepackage{graphicx}
    \\begin{document}
    """
    postamble = "\\end{document}"

    # Get all Beamer files in the output directory
    beamer_files = sorted(
        [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".tex")],
        key=lambda x: int(re.search(r"_page_(\d+)\.tex", x).group(1))  # Sort by page number
    )

    # Write to final output file
    with open(output_file, "w", encoding="utf-8", errors="replace") as f_out:
        f_out.write(preamble + "\n")
        for beamer_file in beamer_files:
            with open(beamer_file, "r", encoding="utf-8", errors="replace") as f_in:
                f_out.write(f_in.read() + "\n")
        f_out.write(postamble + "\n")


def main(pdf_path):
    # Process PDF
    file_name = pdf_path.split("\\")[-1].split('.')[0]

    # Create output directories
    os.makedirs(f"{file_name}_images", exist_ok=True)
    os.makedirs(f"{file_name}_temp", exist_ok=True)
    os.makedirs(f"{file_name}_beamers", exist_ok=True)

    content = extract_pdf_content(pdf_path, images_dir=f"{file_name}_images")

    for i, page_data in enumerate(content):
        if i <= 27:
            continue

        # Convert page to image
        base64_img = convert_page_to_image(pdf_path, page_data["page_num"], output_dir=f"{file_name}_temp")

        # Generate Beamer frame
        frame_code = generate_beamer_frame(page_data, base64_img)
        # frames.append(frame_code)
        print(f"Processed page {page_data['page_num'] + 1}")

        # Create LaTeX document
        output_beamer_file = f'{file_name}_beamers/{file_name}_page_{i}.tex'
        create_latex_document(frame_code, output_file=output_beamer_file)
        print(f"LaTeX Beamer file created: {output_beamer_file}")

    # Concatenate all Beamer files into a single document
    output_beamer_file = f"{file_name}_full.tex"
    concat_beamer_files(output_dir=f"{file_name}_beamers", output_file=output_beamer_file)
    print(f"Concatenated LaTeX Beamer file created: {output_beamer_file}")


if __name__ == "__main__":
    main(r'C:\Users\yufei\OneDrive\Research\Teaching\cmu_lec1_intro.pdf')