
import streamlit as st
import subprocess
import os
import random

st.title("🎥 TikTok Video Generator - Zoom + Blur + Filtros")

st.markdown("Envie seus vídeos e gere um vídeo estilo TikTok com efeitos personalizados!")

# Upload dos cortes e tutorial
cortes = st.file_uploader("Envie os vídeos de cortes", type=["mp4"], accept_multiple_files=True)
video_tutorial = st.file_uploader("Envie o vídeo pronto/tutorial (será inserido automaticamente)", type="mp4")

# Opções do usuário
zoom = st.slider("Zoom Central (1.0 = normal)", 1.0, 2.0, 1.2, 0.1)
blur_strength = st.slider("Intensidade do Blur", 1, 50, 10)
velocidade = st.slider("Velocidade do Vídeo", 0.5, 2.0, 1.0, 0.1)

st.write("### Filtros no Fundo")
ativar_sepia = st.checkbox("Sépia", value=True)
ativar_granulado = st.checkbox("Granulado")
ativar_pb = st.checkbox("Preto e Branco Leve")
ativar_vignette = st.checkbox("Vignette")

st.write("### Outros")
ativar_espelhar = st.checkbox("Espelhar Vídeo", value=True)
ativar_filtro_cor = st.checkbox("Filtro de Cor (Contraste/Saturação)", value=True)

if st.button("Gerar Vídeo"):
    if not cortes or not video_tutorial:
        st.error("❌ Envie os vídeos para continuar.")
    else:
        with open("tutorial.mp4", "wb") as f:
            f.write(video_tutorial.read())

        cortes_names = []
        for idx, corte in enumerate(cortes):
            nome = f"corte_{idx}.mp4"
            with open(nome, "wb") as f:
                f.write(corte.read())
            cortes_names.append(nome)

        # Criar cortes menores de 5s
        cortes_prontos = []
        for c in cortes_names:
            dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "default=noprint_wrappers=1:nokey=1", c], stdout=subprocess.PIPE).stdout.decode().strip()
            try:
                d = float(dur)
                if d > 5:
                    ini = random.uniform(0, d - 5)
                    out = f"cut_{random.randint(1000,9999)}.mp4"
                    subprocess.run(["ffmpeg", "-ss", str(ini), "-i", c, "-t", "5", "-c:v", "libx264", "-preset", "fast", "-crf", "23", out], stdout=subprocess.PIPE)
                    cortes_prontos.append(out)
            except:
                continue

        lista = "lista.txt"
        with open(lista, "w") as f:
            for c in cortes_prontos:
                f.write(f"file '{c}'\n")

        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", lista, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "video_raw.mp4"], stdout=subprocess.PIPE)

        # Filtro Complexo
        filtro = f"[0:v]split=2[main][bg];[main]scale=iw*{zoom}:ih*{zoom},setpts=PTS/{velocidade}"
        if ativar_espelhar: filtro += ",hflip"
        filtro += "[zoomed];"
        if ativar_filtro_cor:
            filtro += "[zoomed]eq=contrast=1.1:saturation=1.2[zoomed];"
        filtro += f"[bg]scale=720:1280,boxblur={blur_strength}:1"
        if ativar_sepia:
            filtro += ",colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
        if ativar_granulado:
            filtro += ",noise=alls=20:allf=t+u"
        if ativar_pb:
            filtro += ",hue=s=0.3"
        if ativar_vignette:
            filtro += ",vignette"
        filtro += "[blur];[blur][zoomed]overlay=(W-w)/2:(H-h)/2"

        subprocess.run(["ffmpeg", "-i", "video_raw.mp4", "-filter_complex", filtro, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "video_editado.mp4"], stdout=subprocess.PIPE)

        # Inserir tutorial
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "video_editado.mp4"], stdout=subprocess.PIPE).stdout.decode().strip()
        dur_f = float(dur)
        pt = random.uniform(5, dur_f - 5)

        subprocess.run(["ffmpeg", "-ss", "0", "-i", "video_editado.mp4", "-t", str(pt), "-c:v", "libx264", "part1.mp4"], stdout=subprocess.PIPE)
        subprocess.run(["ffmpeg", "-ss", str(pt), "-i", "video_editado.mp4", "-c:v", "libx264", "part2.mp4"], stdout=subprocess.PIPE)

        with open("final.txt", "w") as f:
            f.write("file 'part1.mp4'\nfile 'tutorial.mp4'\nfile 'part2.mp4'\n")

        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "final.txt", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "video_final.mp4"], stdout=subprocess.PIPE)

        st.success("✅ Vídeo gerado com sucesso!")
        with open("video_final.mp4", "rb") as f:
            st.download_button("👁️ Baixar Vídeo Final", f, file_name="video_tiktok.mp4")
