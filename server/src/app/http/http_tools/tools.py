import json
import os
import time

import jieba
import requests
from common.common import common_tools 
from config import config
from data.server import Data

class http_tools(object):
    @staticmethod
    def write_event_post_item(data,res):
        for item in data['post_items']:
            item_url = http_tools.get_post_item(item)
            params = {
                'case_id':res['id'],
                'post_item':item_url,
                'c_time':int(time.time()),
                'raw_url':item,
                'is_download':1,
            }
            Data.insert('case_post_item',params)

    @staticmethod
    def get_post_item(item_url):
        file_tail = item_url.split('/')[-1].split('.')[-1]
        if file_tail in config.file_name:
            # 图片文件
            r = requests.get(item_url)
            content = str(r.content)
            file_name = common_tools.get_md5(content)

            running_path =os.path.abspath('.')
            path = running_path.split('/')
            client_path = path[:-2]
            client_path.append(config.file_path)
            client_path = '/'.join(client_path)

            open(client_path+file_name+'.'+file_tail,'wb').write(r.content)
            item_url = config.file_url+file_name+'.'+file_tail

        return item_url
        # 存入本地
    @staticmethod
    def split_case_info(case):
        strip_word_list = ['\n', ' ']
        title = common_tools.decode_base64(case['title'])
        content = common_tools.decode_base64(case['content'])
        title_list = list(jieba.cut_for_search(title))
        content_list = list(jieba.cut_for_search(content))
        case_list = title_list+content_list
        case_word_list = list(set(case_list))

        # print(case_list)
        for word in case_word_list:
            if word not in strip_word_list:
                word_md5 = common_tools.get_md5(word)
                res = Data.find('case_search_index',[('case_id','=',case['id']),('keyword_md5','=',word_md5)])
                if res != None:
                    # print('已经存在')
                    continue
                params = {
                    'case_id':case['id'],
                    'keyword':common_tools.get_base64(word.encode('utf-8')),
                    'keyword_md5':word_md5
                }
                Data.insert('case_search_index',params)
                continue
            else:
                continue

    @staticmethod
    def search_case_by_case_id(case_id,character='player'):
        cond = [('id','=',case_id)]
        if character == 'admin':
            cond.append(('is_show', '=', 1)),

        line = Data.find('case_info', cond)
        if line == None:
            return

        info_line = {
            'case_id': line['id'],
            'content': common_tools.decode_base64(line['content']),
            'c_time': common_tools.time_to_str(line['c_time']).split()[0],
            'title': line['title'],
            'uploader_info': http_tools.get_uploader_info(line['user_id']),
            'post_items': http_tools.get_post_items(line['id']),

        }
        result = info_line
        return result


    @staticmethod
    def get_uploader_info(user_id):
        # 获取上传者信息
        res = Data.find('admin', [('id', '=', user_id)])
        result = {
            'nickname': res['username'],
        }
        return result

    @staticmethod
    def get_post_items(case_id):
        # 获取案子相关附件
        result = []
        res = Data.select('case_post_item', [('case_id', '=', case_id)])
        if res != None:
            for line in res:
                result.append(line['post_item'])

        return result
