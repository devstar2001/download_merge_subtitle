from django.conf import settings
from celery import shared_task, current_task
import logging
from datetime import datetime
import os, sys
from DownAndMerge.celery import app
from celery.utils.log import get_task_logger, get_logger
import json
from pytube import YouTube

def simplify(path):
    # Make sure we get rid of quote characters in file name
    return path.replace('"', '').replace('\'', '').replace(',', '').replace('|','').replace('.','')\
        .replace(' ', '_').replace(':', '')



@shared_task
def merge_subtitle(video_url, itag, lang):
    task_id = current_task.request.id
    state = "STARTED"
    progress_info = "Started"
    current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    try:
        yt = YouTube(video_url)
    except Exception as e:
        print(e)
        state = progress_info = "Failed"
        current_task.update_state(state=state, meta=make_context(progress_info, task_id))
        return state
    title = simplify(yt.title)
    print(title)
    streams = yt.streams.all()
    progress_info = "All steams gained."
    current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    res = None
    ext = None
    for s in streams:
        # print(s)
        if s.itag == itag:
            res = s.resolution
            ext = s.subtype
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(BASE_DIR)
    if not os.path.exists(BASE_DIR + '/static_files/avi'):
        os.mkdir(BASE_DIR + '/static_files/avi')
    if not lang == '':
        caption = yt.captions.get_by_language_code(lang)
        captions = caption.generate_srt_captions()
        print(captions)
        with open(BASE_DIR + '/static_files/avi/' + title + "_" + lang + '.srt', 'w', encoding="utf-8") as f:
            f.write(captions)

        state = progress_info = "Subtitle file created."
        current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    print("downloading start!")
    state = progress_info = "Downloading start."
    print(title + "_" + res)

    if os.path.exists(BASE_DIR + '/static_files/avi/' + title + "_" + res):
        os.remove(BASE_DIR + '/static_files/avi/' + title + "_" + res)

    current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    yt.streams.get_by_itag(itag).download(BASE_DIR + '/static_files/avi/', filename=title + "_" + res)
    print("downloading done!")
    state = progress_info = "Downloading done."
    current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    if lang == '':
        state = progress_info = "COMPLETED"
        current_task.update_state(state=state, meta=make_context(progress_info, task_id))
        return title + "_" + res + '.' + ext
    command = 'ffmpeg -i "%s" -vf subtitles="%s"  "%s"'
    original = BASE_DIR + '/static_files/avi/' + title + "_" + res + "." + ext
    subtitles = BASE_DIR + '/static_files/avi/' + title + "_" + lang + ".srt"

    merged_filename = title + "_" + res + "_" + lang + ".srt." + "avi"
    merged_path = BASE_DIR + "/static_files/avi/" + merged_filename
    if os.path.exists(merged_path):
        os.remove(merged_path)
    # merged = title + ".srt." + ext
    command = command % (original, subtitles, merged_path)
    print(command)
    print("merging start!")
    state = progress_info = "Merging started."
    current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    os.system(command)
    print("merging done!")
    state = progress_info = "Merging done."
    current_task.update_state(state=state, meta=make_context(progress_info, task_id))

    state = progress_info = "COMPLETED"
    current_task.update_state(state=state, meta=make_context(progress_info, task_id))
    return merged_filename


def make_context(progress_info, task_id):
    context = {
        'progress_info': progress_info,
        'task_id': task_id
    }
    return context
