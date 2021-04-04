import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from posts.models import Group, Post, User


@override_settings(MEDIA_ROOT='temp_media')
class FieldPostGroupModelTest(TestCase):
    """Class Test for K: verbose name, help text field.
    And expected self methods.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='Слаг',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            group=cls.group,
            author=User.objects.create(username='tester'),
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_verbose_name(self):
        """For custom form models, a human-readable name -
        (verbose name) is specified.
        """

        post = FieldPostGroupModelTest.post
        field_verbose = {
            'text': 'Тело поста',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        """Help text is specified for custom form models."""

        post = FieldPostGroupModelTest.post
        field_help_text = {
            'text': 'Наполнить пост',
            'group': 'Выбор группы не обязателен, но желателен',
            'image': 'Выобор картинки',
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_object_name_is_title_field(self):
        """The title field has a display,
        when requesting an object from a queryset,
        in the readable format __str__, returns the expected result.
        """

        group = FieldPostGroupModelTest.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group))

    def test_str_post(self):
        """String length limitation for queryset,
        returns the expected result [~: 15].
        """

        post = FieldPostGroupModelTest.post
        expected_length_string = post.text[:15]
        self.assertEquals(expected_length_string, str(post))
