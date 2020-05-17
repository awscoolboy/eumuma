from selenium import webdriver
import time
from config import password, username, apikey, video_height, video_width, url
from pyyoutube import Api
from embeddify import Embedder
import isodate
from selenium.webdriver.common.action_chains import ActionChains
from dbhelper import DBHelper
from selenium.webdriver.support.ui import Select


class Lesson():
    def __init__(self, title, code, duration):
        self.title = title
        self.code = code
        self.duration = duration


class Course():
    def __init__(self, title, playlistId, start):
        self.title = title
        self.playlistId = playlistId
        self.start = start


class EdumaBot():
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.api = Api(api_key=apikey)
        self.db = DBHelper()

    def login(self):
        self.driver.get(url)

        time.sleep(1)
        login_btn = self.driver.find_element_by_xpath('//*[@id="wp-submit"]')
        email_field = self.driver.find_element_by_xpath('//*[@id="user_login"]')
        pass_field = self.driver.find_element_by_xpath('//*[@id="user_pass"]')

        email_field.send_keys(username)
        time.sleep(1)
        pass_field.send_keys(password)
        login_btn.click()
        self.driver.find_element_by_xpath('//*[@id="toplevel_page_learn_press"]').click()
        self.driver.find_element_by_xpath('//*[@id="toplevel_page_learn_press"]/ul/li[3]/a').click()
        self.driver.find_element_by_xpath('//*[@id="wpbody-content"]/div[3]/a').click()


    def start(self):
        self.login()
        courses = []
        # resume_lesons = self.db.get_resume_lessons()
        #
        # print(resume_lesons.rowcount)
        #
        # if resume_lesons.rowcount != -1:
        #     for ressume_lesson in resume_lesons:
        #         index = ressume_lesson[4]
        #         total = ressume_lesson[3]
        #         title = ressume_lesson[2]
        #         playlist_id = ressume_lesson[1]
        #
        #         if int(index) == int(total):
        #             continue
        #
        #         print("found lesons that is not added index = {} ,playlist = {},count = {} ".format(index, playlist_id,
        #                                                                                             total))
        #         courses.append(Course(title=str(title), playlistId=str(playlist_id), start=str(index + 1)))

        f = open("playlist", "r+")
        for i in f:
            k = i.split('\n')
            for j in k:
                vals = j.split("[|]")
                if len(vals) == 2:
                    courses.append(Course(title=str(vals[1]), playlistId=str(vals[0]), start=0))

        if len(courses) == 0:
            print("no lesson found on file =  " + f.name)
            return

        print("course found on file " + str(len(courses)))

        for course in courses:

            finsihed = self.db.getFinishedPlayLists(playlist_id=course.playlistId)
            print(finsihed)
            if finsihed.rowcount != -1:
                print("course already exist titile =  " + course.title)
                continue

            playlist_item_by_playlist = self.api.get_playlist_items(playlist_id=course.playlistId, count=1000)
            videos = playlist_item_by_playlist.items
            print("number of vidoes in playlist = " + str(len(videos)))
            if len(videos) <= 0:
                print("no videos found for  playlist = " + str(course.playlistId) + "\n")
                continue
            count = 1
            real_video_count = len(videos)
            lesson_list = []



            temp_counter = 0
            for video in videos:

                temp_counter = temp_counter + 1
                if temp_counter <=  -1 and course.playlistId == "":
                    continue



                count = temp_counter

                video_by_id = self.api.get_video_by_id(video_id=video.snippet.resourceId.videoId,
                                                       parts=('snippet', 'contentDetails', 'statistics'))
                if len(video_by_id.items) <= 0:
                    print("missed or private vidoe for  = " + str(course.playlistId) + "\n")
                    real_video_count = real_video_count - 1
                    continue

                item = video_by_id.items[0]
                title = course.title + " " + self.formatLessonName(count) + " " + item.snippet.title



                time_val = isodate.parse_duration(item.contentDetails.duration)
                code = self.getYoutubeEmbedCode(video.snippet.resourceId.videoId)
                count = count + 1
                lesson = Lesson(title, code, time)

                title_field = self.driver.find_element_by_xpath('//*[@id="title"]')
                media_field = self.driver.find_element_by_xpath('//*[@id="_lp_lesson_video_intro"]')
                date_field = self.driver.find_element_by_xpath('//*[@id="_lp_duration"]')
                publish_button = self.driver.find_element_by_xpath('//*[@id="publish"]')
                select = Select(self.driver.find_element_by_id('_lp_duration_select'))

                time_array = str(time_val).split(":")

                print(time_array[0] + " = hour")
                print(time_array[1] + " = minties")

                final_time = 1
                if time_array[0] != "0" and time_array[0] != "00":
                    select.select_by_value('hour')
                    final_time = time_array[0]
                elif time_array[1] != "0" and time_array[1] != "00":
                    select.select_by_value('minute')
                    final_time = time_array[1]
                else:
                    select.select_by_value('minute')

                title_field.clear()
                title_field.send_keys(lesson.title)
                time.sleep(1)
                media_field.clear()
                media_field.send_keys(lesson.code)
                time.sleep(1)
                date_field.clear()
                date_field.send_keys(final_time)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", publish_button)
                self.driver.implicitly_wait(10)
                time.sleep(2)
                self.driver.find_element_by_xpath('//*[@id="wpbody-content"]/div[3]/a').click()
                self.driver.implicitly_wait(10)
                #self.db.update_lessons_resume(playlist_id=course.playlistId, index=str(temp_counter))

            # suffucly addded the playlsit
           # self.db.add_finished_playlist(course.playlistId)
           # self.db.delete_course_from_resume(playlist_id=course.playlistId)

    def formatLessonName(self, count):
        countStr = ""
        if count <= 9:
            countStr = "00" + str(count)
        elif count <= 99 and count >= 10:
            countStr = "0" + str(count)
        else:
            countStr = str(count)
        return countStr


    def getYoutubeEmbedCode(self, videoId):
        embedder = Embedder()
        code = embedder("https://www.youtube.com/watch?v=" + str(videoId), width=video_width, height=video_height)
        return code


bot = EdumaBot()
bot.start()