def describir_sujeto_base(imagen_bytes):
    img = Image.open(io.BytesIO(imagen_bytes))
    instruccion = (
        "Describe ONLY the structural content, key figures, pose, layout, and symbolic elements in this image. "
        "Strictly DO NOT mention colors, medium, or whether it is black and white, sketch, or monochrome. "
        "Keep it to one concise English sentence focused purely on what is depicted physically."
    )
    respuesta = client_gemini.models.generate_content(
        model="gemini-3.6-flash",
        contents=[img, instruccion]
    )
    return respuesta.text.strip()

def generar_con_estilo(sujeto, estilo):
    # Imponemos el ADN del estilo y la paleta de color sobre la estructura base
    prompt_final = (
        f"{sujeto}, fully reimagined in {estilo}, deep pitch-black background, "
        f"radiant glowing pure gold accents (#FFD700), highly detailed authentic skin and fabric textures, "
        f"cinematic rim lighting, edge-to-edge full scene composition, no circular framing, no borders, masterpiece"
    )
    prompt_encoded = urllib.parse.quote(prompt_final)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true&model=flux"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    res = requests.get(url, headers=headers, timeout=90)
    if res.status_code == 200 and len(res.content) > 5000:
        return res.content
    return None
