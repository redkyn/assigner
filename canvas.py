import http.client
import json
import logging
import time

__author__ = 'Islam Elnabarawy'


class CanvasAPI:
    REQUEST_HEADER = {
        "Authorization": "Bearer ",
        "Content-Type": "application/json"
    }
    WEBSITE_ROOT = "https://mst.instructure.com"

    def __init__(self, canvas_token):
        self.REQUEST_HEADER['Authorization'] += canvas_token

    def _request(self, method: str, url: str, params: dict = None, retries: int = 3) -> http.client.HTTPResponse:
        tries = 0
        while tries <= retries:
            try:
                connection = http.client.HTTPSConnection('mst.instructure.com', 443)
                connection.connect()
                header = self.REQUEST_HEADER
                connection.request(method, url, (json.dumps(params) if params is not None else None), header)
                return connection.getresponse()
            except Exception as ex:
                tries += 1
                if tries > retries:
                    raise ex
                logging.warning("Caught exception in request after %d tries. Will retry %d more times.",
                                tries, retries - tries, exc_info=True)
                time.sleep(1)

    @staticmethod
    def _decode_links(link):
        links = link.split(',')
        result = {}
        for l in links:
            f, s = l.split(';')
            result[s[6:-1]] = f[1:-2].replace(CanvasAPI.WEBSITE_ROOT, '')
        return result

    def _get_all_pages(self, url: str, params: dict = None) -> list:
        response = self._request('GET', url, params)
        result = json.loads(response.read().decode())
        links = CanvasAPI._decode_links(response.getheader("Link"))
        count = len(result)
        page = 1
        while 'next' in links:
            logging.debug("Got links:\n" + json.dumps(links, sort_keys=True, indent=2))
            page += 1
            next_url = url.split('?')[0] + '?page=%s&per_page=%s' % (page, count)
            logging.info("Getting next page for " + url + " via " + next_url)
            response = self._request('GET', next_url, params)
            result.extend(json.loads(response.read().decode()))
            links = CanvasAPI._decode_links(response.getheader("Link"))

        return result

    def get_teacher_courses(self):
        result = self._get_all_pages('/api/v1/courses',
                                     {'enrollment_type': 'teacher', 'state': ['available']})
        return result

    def get_course_students(self, course_id):
        result = self._get_all_pages('/api/v1/courses/%s/users?per_page=50' % course_id,
                                     {'enrollment_type': ['student'], 'enrollment_state': ['active']})
        return result
