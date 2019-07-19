import os
from pytube import YouTube

def check(video_url):
    # Check if it is a url
    if video_url.startswith('https://') or video_url.startswith('http://'):
        return True
    return False

def simplify(path):
    # Make sure we get rid of quote characters in file name
    return path.replace('"', '').replace('\'', '').replace(',', '').replace('|','').replace('.','')


if __name__ == '__main__':
    while True:
        video_url = str(input('please input youtube url.\n'))
        if not check(video_url):
            print("This is not url format.\n")
        else:
            print("ok. url = ", video_url)
            break
    yt = YouTube(video_url)
    try:
        yt = YouTube(video_url)
    except Exception as e:
        print(e)
        from pytube import Playlist
        pl = Playlist(video_url)
        pl.download_all()
        exit(-1)


    title = simplify(yt.title)
    title = title.replace(' ', '_')
    print(title)
    # streams = yt.streams.filter().all()
    streams = yt.streams.filter(progressive=True).all()
    while True:
        yesno = input('do you want to download ? y/n\n')
        if yesno == 'n':
            exit()
        else:
            itag = None
            res = None
            for s in streams:
                print(s)
            ext = ''
            while True:
                itag = input('please input itag to select resolution.\n')
                f = False
                no_res = False
                for s in streams:
                    if s.itag == itag:
                        if s.resolution is None:

                            no_res = True
                            break
                        res = s.resolution
                        ext = s.mime_type.split("/")[1]
                        f = True
                        break
                if f :
                    break
                else:
                    if no_res:
                        print('itag format is not correct. please type again.\n')
                    else:
                        print('itag no exist. please type again.\n')

            print("downloading start!")
            try:
                if itag:
                    # yt.streams.first().download(filename=title + "_" + res)
                    yt.streams.get_by_itag(itag).download('../' , filename=title + "_" + res)
                else:
                    yt.streams.first().download(filename=title + "_" + res)
                print("downloading success!")
            except Exception as e2:
                print(e2)
                print("downloading failed!")
            captions = yt.captions.all()
            if not len(captions) == 0:
                for c in captions:
                    print(c)
                lan_code = ""
                while True:
                    lan = input('Please type code to select language. i.e: en \n')
                    lan_code = None
                    for c in captions:
                        if lan in c.code:
                            lan_code = c.code
                    if lan_code:
                        break
                    else:
                        print("That language no exist. please input other.\n")

                caption = yt.captions.get_by_language_code(lan_code)
                captions = caption.generate_srt_captions()
                print(captions)
                with open(title + "_" + lan_code + '.srt', 'w', encoding="utf-8") as f:
                    f.write(captions)


                command = 'ffmpeg -i %s -vf subtitles=%s  %s'
                # command = 'ffmpeg -i "%s" -i "%s" -c:v copy -c:a copy -c:s mov_text "%s"'

                original = title + "_" + res + "." + ext
                subtitles = title + "_" + lan_code + ".srt"
                merged = title + "_" + res + "_" + lan_code + ".srt." + "avi"
                # merged = title + ".srt." + ext
                command = command % (original, subtitles, merged)
                print(command)
                print("merging start!")
                os.system(command)
                print("merging done!")







    # while True:
    #     converting = str(input('Do you want to convert video in continue? y/n : '))
    #     if converting == 'y':
    #         break
    #
    # command = 'ffmpeg -i "%s" -vf scale=320:-1 "%s"'
    # command = command % (merged, subtitles+"_320.mp4")
    # print("320p converting start!")
    # os.system(command)
    # print("320p converting done!")
    #
    # command = 'ffmpeg -i "%s" -vf scale=120:-1 "%s"'
    # command = command % (merged, subtitles+"_120.mp4")
    # print("120p converting start!")
    # os.system(command)
    # print("120p converting done!")