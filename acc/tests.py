from os.path import basename

import responses

from elk.utils.testing import TestCase, create_user

from .pipelines import SaveSocialProfile


class TestSaveSocialProfile(SaveSocialProfile):
    source_name = 'testsrc'
    extension = 'jpgtest'

    def get_picture_url(self):
        return 'http://testing.test/testpic.jpg'

    @responses.activate
    def fetch_picture(self):
        return super().fetch_picture()


class TestSocialPipeline(TestCase):
    def test_fetch_picture(self):
        responses.add(responses.GET,
                      'http://testing.test/testpic.jpg',
                      body=b'testbytes',
                      status=200,
                      content_type='image/jpeg'
                      )

        profile_saver = TestSaveSocialProfile(user='', response='', backend='')
        profile_saver.fetch_picture()
        self.assertEqual(profile_saver.profile_picture.read(), b'testbytes')

    def test_save_source(self):
        user = create_user()

        class TestBackend:
            name = 'social-test-source-name'

        profile_saver = TestSaveSocialProfile(user=user, response='', backend=TestBackend)
        profile_saver.save_social_source()

        self.assertEqual(user.crm.source, 'social-test-source-name')

    def test_save_picture(self):
        user = create_user()
        responses.add(responses.GET,
                      'http://testing.test/testpic.jpg',
                      body=b'testbytes',
                      status=200,
                      content_type='image/jpeg'
                      )

        profile_saver = TestSaveSocialProfile(user=user, response='', backend='')
        profile_saver.fetch_picture()

        profile_saver.save_picture()

        self.assertEqual(basename(user.crm.profile_photo.name), '%s-testsrc.jpgtest' % user.username)
        self.assertEqual(user.crm.profile_photo.read(), b'testbytes')
