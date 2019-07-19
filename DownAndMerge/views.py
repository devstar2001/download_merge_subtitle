import os
from django.http import HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
import pytube.exceptions
from pytube import YouTube
from .forms import DownloadForm
import urllib.parse
from .tasks import merge_subtitle
import json
from celery.result import AsyncResult
def check(video_url):
    # Check if it is a url
    if video_url.startswith('https://') or video_url.startswith('http://'):
        return True
    return False

def simplify(path):
    # Make sure we get rid of quote characters in file name
    return path.replace('"', '').replace('\'', '').replace(',', '').replace('|','').replace('.','')

def list_video(request):
    pass
    global context
    form = DownloadForm(request.POST or None)
    if form.is_valid():
        video_url = form.cleaned_data.get("url")
        if 'm.' in video_url:
            video_url = video_url.replace(u'm.', u'')

        # elif 'youtu.be' in video_url:
        #     video_id = video_url.split('/')[-1]
        #     video_url = 'https://www.youtube.com/watch?v=' + video_id

        # if len(video_url.split("=")[-1]) != 11:
        #     return HttpResponse('Enter correct url.')
        if not check(video_url):
            return HttpResponse("This is not url format.")

        try:
            yt = YouTube(video_url)
        except Exception as e:
            print(e)
            return render(request, 'home.html', {'error_info': 'Please try again.'})
        title = simplify(yt.title)
        print(title)
        # streams = yt.streams.all()
        streams = yt.streams.filter(progressive=True).all()
        video_audio_streams = []
        for s in streams:
            # print(s)
            if s.resolution:
                video_audio_streams.append({
                    'itag': s.itag,
                    'resolution': s.resolution,
                    'extension': s.subtype,
                    # 'file_size': filesizeformat(s.filesize),
                    # 'video_url': s.url + "&title=" + title
                })
        captions = yt.captions.all()
        caption_codes = []
        for c in captions:
            print(c)
            caption_codes.append({
                'code': c.code,
                'lang': c.name
            })

        context = {
            'form': form,
            'title': title,
            'stream_video': video_audio_streams,
            'streams': video_audio_streams,
            'description': yt.description,
            # 'thumb': yt.thumbnail_url,
            'duration': yt.length,
            'views': yt.views,
            'subtitle_lang': caption_codes,
            'video_url': video_url

        }

        return render(request, 'home.html', context)

    return render(request, 'home.html', { 'form': form })


def clean_storage(request):
    import shutil
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(BASE_DIR + '/static_files/avi/'):
        shutil.rmtree(BASE_DIR + '/static_files/avi/')
    data = {'message':'Ok'}
    return HttpResponse(json.dumps(data), content_type='application/json')


def merge_video(request):
    job_id,video_url, itag, lang = None, None, None, None
    if 'video_url' in request.POST:
        video_url = request.POST['video_url']
    if 'lang' in request.POST:
        lang = request.POST['lang']
    if 'itag' in request.POST:
        itag = request.POST['itag']
    if 'job_id' in request.POST:
        job_id = request.POST['job_id']
    if job_id is None:
        # job = merge_subtitle(video_url, itag, lang)
        job = merge_subtitle.delay(video_url, itag, lang)
        job_id = job.id
        send_data = {'job_id': job_id}
        json_data = json.dumps(send_data)
        return HttpResponse(json_data, content_type="application/json")
    else:
        job = AsyncResult(job_id)
        if job.state == 'SUCCESS' and not job.result == 'Failed':
            download_url = request._current_scheme_host + '/static/avi/' + job.result
            context = {
                'job_id': str(job_id),
                'state': job.state,
                'download_url': download_url
            }
        else:
            if job.result == 'Failed':
                context = {
                    'job_id': str(job_id),
                    'state': 'Failed',

                }
            else:
                context = {
                    'job_id': str(job_id),
                    'state': job.state,
                    'info': job.result
                }
        json_data = json.dumps(context)
        return HttpResponse(json_data, content_type="application/json")
