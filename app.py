import streamlit as st
import PyPDF2
import pikepdf
import pdfplumber

# Spine width calculation (80gsm bond default)
def calculate_spine_width(page_count, gsm=80):
    thickness_per_page = 0.08 if gsm == 80 else 0.1
    return round((page_count / 2) * thickness_per_page, 2)

# DPI Check
def check_image_dpi(pdf_path, min_dpi=300):
    low_res_images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            for img in page.images:
                dpi_x = img["width"] / (img["x1"] - img["x0"]) * 72
                dpi_y = img["height"] / (img["y1"] - img["y0"]) * 72
                if dpi_x < min_dpi or dpi_y < min_dpi:
                    low_res_images.append((page_num, dpi_x, dpi_y))
    return low_res_images

# Font embedding check
def check_fonts_embedded(pdf_path):
    embedded = True
    missing_fonts = []
    with pikepdf.open(pdf_path) as pdf:
        for font in pdf.get_object(pdf.root.Res / "Font", default={}):
            font_dict = pdf.get_object(font)
            if "/FontFile" not in font_dict and "/FontFile2" not in font_dict:
                embedded = False
                missing_fonts.append(str(font))
    return embedded, missing_fonts

st.title("📘 Preflight PDF Checker")
st.write("Upload your print-ready PDF to check for prepress compliance.")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    pdf_path = "temp.pdf"

    pdf_reader = PyPDF2.PdfReader(pdf_path)
    num_pages = len(pdf_reader.pages)

    st.subheader("Report")
    st.write(f"Total Pages: {num_pages}")

    # Page size & orientation
    sizes = []
    orientations = []
    for page in pdf_reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        sizes.append((w, h))
        orientations.append("Portrait" if h > w else "Landscape")
    st.write("Page Sizes (first 5 shown):", sizes[:5])
    st.write("Page Orientations (first 5 shown):", orientations[:5])

    # Binding type selection
    binding = st.selectbox("Binding Type", ["Saddle Stitch", "Perfect Bound", "Wiro Binding"])
    if binding == "Perfect Bound":
        if num_pages < 60:
            st.warning("Perfect binding requires at least 60 pages.")
        else:
            spine = calculate_spine_width(num_pages, 80)
            st.write(f"Calculated Spine Width: {spine} mm")

    # Colour vs. B/W
    bw_only = True
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if "c" in page.objects["char"][0].keys():  # quick check for colour info
                bw_only = False
                break
    st.write("Pages are:", "Black & White only" if bw_only else "Contain Colour")

    # Fonts
    embedded, missing = check_fonts_embedded(pdf_path)
    if embedded:
        st.success("All fonts embedded ✅")
    else:
        st.error(f"Missing font embedding: {missing}")

    # Image DPI
    low_dpi = check_image_dpi(pdf_path)
    if low_dpi:
        st.warning("Low-resolution images found:")
        for page_num, dpi_x, dpi_y in low_dpi:
            st.write(f"Page {page_num}: {dpi_x:.1f}x{dpi_y:.1f} DPI")
    else:
        st.success("All images meet minimum DPI ✅")
