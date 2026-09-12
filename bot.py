def extraer_adn_de_estilo(imagen_bytes):
    img = Image.open(io.BytesIO(imagen_bytes))
    instruccion = (
        "You are an expert visual prompt engineer. Analyze this image's exact artistic style, lighting, and palette. "
        "Create a condensed prompt (under 60 words) focused strictly on reproducing this visual signature: "
        "pitch black background, glowing liquid gold and crystalline textures, sacred geometry lines, glowing volumetric amber lighting, "
        "hyper-detailed 3D render, dark luxury metaphysical aesthetic, floating radiant gold particles. "
        "Do not mention specific people or objects, only the visual medium, colors, and lighting. Return only the prompt in English."
    )
    respuesta = client_gemini.models.generate_content(
        model="gemini-3.6-flash",
        contents=[img, instruccion]
    )
    return respuesta.text.strip()

def describir_sujeto_base(imagen_bytes):
    img = Image.open(io.BytesIO(imagen_bytes))
    instruccion = (
        "Describe the visual composition, key subjects, and structural layout of this image in one concise English phrase "
        "(e.g., 'Three wise men riding camels across a desert towards a radiant celestial star, with intricate astrological charts and nativity scene layout')."
    )
    respuesta = client_gemini.models.generate_content(
        model="gemini-3.6-flash",
        contents=[img, instruccion]
    )
    return respuesta.text.strip()

def generar_con_estilo(sujeto, estilo):
    # Prohibimos marcos circulares/medallones y forzamos composición panorámica horizontal
    prompt_final = (
        f"wide landscape panoramic composition, {sujeto}, {estilo}, solid pitch black background, "
        f"vibrant luminescent pure gold (#FFD700), open wide angle scene, no borders, no circular frames, "
        f"extreme contrast, intricate technical linework, 8k octane render, masterpiece"
    )
    prompt_encoded = urllib.parse.quote(prompt_final)
    # Cambiamos resolución a panorámica 16:9 real (1280x720)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&nologo=true&model=flux"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    res = requests.get(url, headers=headers, timeout=90)
    if res.status_code == 200 and len(res.content) > 5000:
        return res.content
    return None
