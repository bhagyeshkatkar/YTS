from django.shortcuts import render
from .models import Summary
from django.shortcuts import redirect

from io import BytesIO
from django.http import HttpResponse
from xhtml2pdf import pisa

from pytube import YouTube
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
from transformers import pipeline
from youtube_transcript_api import YouTubeTranscriptApi
from IPython.display import YouTubeVideo
from django.shortcuts import render



#Create your views here.
def index(request):
    return render(request,"index.html")


# code which can handle both condition

def home(request):
    if request.method == 'POST':
        if 'video_url' in request.POST:
            video_url = request.POST['video_url']
            video_id = video_url.split('=')[1]
            YouTubeVideo(video_id)

            # Get the video transcript if available
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                result = ""
                for i in transcript:
                    result += ' ' + i['text']
            except:
                transcript = None

            if transcript:
                # Summarize the transcript
                summarizer = pipeline('summarization')
                num_chars_per_iteration = 1000
                summarized_text = []

                for i in range(0, len(result), num_chars_per_iteration):
                    start = i
                    end = i + num_chars_per_iteration
                    out = summarizer(result[start:end])
                    out = out[0]
                    out = out['summary_text']
                    summarized_text.append(out)

                # Render the template with the summary
                return render(request, 'index.html', {'summary': summarized_text})
            else:
                # Step 1: Download and convert YouTube video to audio
                yt = YouTube(video_url)
                yt.streams.filter(only_audio=True, file_extension='mp4').first().download(filename='ytaudio.mp4')

                # Convert audio to WAV format
                audio_file = "ytaudio.mp4"
                wav_file = "ytaudio.wav"

                audio = AudioSegment.from_file(audio_file)
                audio.export(wav_file, format='wav')

                # Step 2: Transcribe the audio
                r = sr.Recognizer()

                def transcribe_audio(path):
                    with sr.AudioFile(path) as source:
                        audio_listened = r.record(source)
                        text = r.recognize_google(audio_listened)
                    return text

                def get_large_audio_transcription_on_silence(path):
                    sound = AudioSegment.from_file(path)
                    chunks = split_on_silence(sound, min_silence_len=500, silence_thresh=sound.dBFS-14, keep_silence=500)
                    folder_name = "audio-chunks"
                    if not os.path.isdir(folder_name):
                        os.mkdir(folder_name)
                    whole_text = ""
                    for i, audio_chunk in enumerate(chunks, start=1):
                        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
                        audio_chunk.export(chunk_filename, format="wav")
                        try:
                            text = transcribe_audio(chunk_filename)
                        except sr.UnknownValueError as e:
                            print(".", str(e))
                        else:
                            text = f"{text.capitalize()}. "
                            print(text)
                            whole_text += text
                    return whole_text

                text = get_large_audio_transcription_on_silence(wav_file)

                # Step 3: Summarize the text
                summarizer = pipeline('summarization')
                num_chars_per_iteration = 1000
                summarized_text = []

                for i in range(0, len(text), num_chars_per_iteration):
                    start = i
                    end = i + num_chars_per_iteration
                    out = summarizer(text[start:end])
                    out = out[0]
                    out = out['summary_text']
                    summarized_text.append(out)

                # Render the template with the summary
                return render(request, 'index.html', {'summary': summarized_text})

    return render(request, 'index.html')



def download_summary(request):
    if request.method == 'POST':
        summary = request.POST.get('summary', '')
        pdf_file = generate_pdf(summary)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="summary.pdf"'
        return response
    else:
        return HttpResponse('Error: Invalid request method.')


def generate_pdf(summary):
    html = f'<html><head><meta charset="UTF-8"><title>Summary</title></head><body><h1>Summary</h1><p>{summary}</p></body></html>'
    pdf_file = BytesIO()
    pisa.CreatePDF(BytesIO(html.encode('UTF-8')), dest=pdf_file, encoding='UTF-8')
    pdf_file.seek(0)
    return pdf_file


def assesment(request):
    summary = Summary.objects.all()
    return render(request,"index.html",{'summary':summary})


