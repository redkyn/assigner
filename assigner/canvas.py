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

    def __init__(self, canvas_token, website_root):
        self.REQUEST_HEADER['Authorization'] += canvas_token
        self.website_root = website_root

    def _request(self, method: str, url: str, params: dict = None, retries: int = 3) -> http.client.HTTPResponse:
        tries = 0
        while tries <= retries:
            try:
                connection = http.client.HTTPSConnection(self.website_root, 443)
                connection.connect()
                header = self.REQUEST_HEADER
                connection.request(method, url, (json.dumps(params) if params is not None else None), header)
                return connection.getresponse()
            except http.client.HTTPException:
                tries += 1
                if tries > retries:
                    raise
                logging.warning("Caught exception in request after %d tries. Will retry %d more times.",
                                tries, retries - tries, exc_info=True)
                time.sleep(1)

    def _decode_links(self, link):
        """
        Extract pagination links from the Canvas API response header's Links field
        :param link: value of the Links field in Canvas API's response header
        :return: A dictionary with the name and value of each link
        """
        links = link.split(',')
        result = {}
        for l in links:
            f, s = l.split(';')
            result[s[6:-1]] = f[1:-1].replace(self.website_root, '')
        return result

    def _get_all_pages(self, url: str, params: dict = None) -> list:
        """
        Get the full results from a query by following pagination links until the last page
        :param url: The URL for the query request
        :param params: A dictionary of parameter names and values to be sent with the request
        :return: The full list of result objects returned by the query
        """
        response = self._request('GET', url, params)
        result = json.loads(response.read().decode())
        links = self._decode_links(response.getheader("Link"))
        count = len(result)
        page = 1
        while 'next' in links:
            logging.debug("Got links:\n%s", json.dumps(links, sort_keys=True, indent=2))
            page += 1
            next_url = url.split('?')[0] + '?page=%s&per_page=%s' % (page, count)
            logging.info("Getting next page for " + url + " via " + next_url)
            response = self._request('GET', next_url, params)
            result.extend(json.loads(response.read().decode()))
            links = self._decode_links(response.getheader("Link"))

        return result

    def get_instructor_courses(self):
        get = lambda x: self._get_all_pages('/api/v1/courses',
                                            {'enrollment_type': x, 'state': ['available']})
        result = get('teacher')
        result.extend(get('ta'))
        result.extend(get('grader'))
        return result

    def get_course_students(self, course_id):
        result = self._get_all_pages('/api/v1/courses/%s/users?per_page=50' % course_id,
                                     {'enrollment_type': ['student'], 'enrollment_state': ['active']})
        return result
