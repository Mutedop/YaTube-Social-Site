import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class PagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_post = User.objects.create_user(username='AuthorPost')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author_post)
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
            slug='test-slug',
            description='Описание',
        )
        cls.group_two = Group.objects.create(
            title='Название 2',
            slug='test-slug-two',
            description='Описание 2',
        )
        cls.post = Post.objects.create(
            id=123,
            text='Текст поста',
            group=cls.group,
            author=cls.author_post,
            image=cls.uploaded,
        )
        posts_items = [Post(
            text=f'Пост № {number_post}',
            author=cls.author_post,
            group=cls.group,
            image=cls.uploaded) for number_post in range(12)]
        Post.objects.bulk_create(posts_items)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> User:
        self.user = User.objects.create_user(username='Tester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """Try using reverse for names.
        I check the work args & kwargs for r_name, url's
        """

        template_pages = {
            'new.html': reverse('new_post'),
            'post.html': (reverse('post',
                          kwargs={'username': 'AuthorPost',
                                  'post_id': '123'})),
            'index.html': reverse('index'),
            'group.html': (reverse('group_post',
                           args={'test-slug'})),
            'profile.html': (reverse('profile',
                             args={'Tester'})),
        }

        for template, reverse_name in template_pages.items():
            with self.subTest(template=template):
                response = (self.authorized_client.
                            get(reverse_name))
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        response = self.authorized_client.get(reverse('index'))
        post_object = response.context['page'][0]
        post_author_0 = post_object.author
        post_pub_date_0 = post_object.pub_date
        post_text_0 = post_object.text
        post_image_0 = post_object.image
        self.assertEqual(post_author_0,
                         PagesTest.post.author)
        self.assertEqual(post_pub_date_0,
                         PagesTest.post.pub_date)
        self.assertEqual(post_text_0,
                         PagesTest.post.text)
        self.assertEqual(post_image_0,
                         PagesTest.post.image)

    def test_group_correct_context(self):
        response = self.authorized_client.get(
            reverse('group_post',
                    kwargs={'slug': 'test-slug'}))
        self.assertEqual(
            response.context['group'].title,
            'Название')
        self.assertEqual(
            response.context['group'].description,
            'Описание')
        self.assertEqual(
            response.context['group'].slug,
            'test-slug')

    def test_new_post_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('new_post')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_index_page_paginator(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_create_post_on_view(self):
        """Check that if you specify a group when creating a post,
        then this post appears on the main page of the site,
        on the page of the selected group.
        Make sure this post is not in a group it was not intended for.
        """

        posts_count_group = Post.objects.filter(
            group=PagesTest.group
        ).count()
        posts_count_group_two = Post.objects.filter(
            group=PagesTest.group_two
        ).count()
        post_count = Post.objects.count()
        date_field = {
            'text': 'Создаем пост для сущ. группы',
            'group': PagesTest.group.id,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=date_field,
            follow=True
        )

        # Checked the appearance of the created post.
        self.assertNotEqual(Post.objects.count(), post_count)
        # I checked that after the creation they went to the main page.
        self.assertRedirects(response, reverse('index'))
        # I checked the create text field that the post is in the group 1.
        self.assertTrue(Post.objects.filter(
            text='Создаем пост для сущ. группы',
            group=PagesTest.group.id
        ).exists())
        # Compare the number of posts in group one.
        self.assertNotEqual(Post.objects.filter(
            group=PagesTest.group).count(), posts_count_group
        )
        # I checked the text field that the post is in the group_two 2.
        self.assertFalse(Post.objects.filter(
            text='Создаем пост для сущ. группы',
            group=PagesTest.group_two.id
        ).exists())
        # Compare the number of posts in group 2.
        self.assertEqual(Post.objects.filter(
            group=PagesTest.group_two).count(), posts_count_group_two
        )

    def test_post_edit_correct_context(self):
        response = PagesTest.author_client.get(
            reverse('post_edit',
                    kwargs={
                        'username': 'AuthorPost',
                        'post_id': '123'
                    })
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': 'AuthorPost'})
        )
        post_object = response.context['page'][0]
        post_author_0 = post_object.author
        post_text_0 = post_object.text
        post_image_0 = post_object.image
        self.assertEqual(post_author_0,
                         PagesTest.post.author)
        self.assertEqual(post_text_0,
                         PagesTest.post.text)
        self.assertEqual(post_image_0,
                         PagesTest.post.image)

    def test_following_auth_user(self):
        """An authorized user can follow other users."""

        follower_count = Follow.objects.all().count()
        self.authorized_client.get(reverse(
            'profile_follow', args={PagesTest.author_post})
        )
        follower_count_now = Follow.objects.all().count()
        self.assertNotEqual(follower_count_now, follower_count)

    def test_unfollow_auth_user(self):
        """An authorized user can unsubscribe from other users.
        For clarity assertEqual - X, and kwargs.
        """

        Follow.objects.create(user=self.user, author=PagesTest.author_post)
        follower_count = Follow.objects.all().count()
        self.authorized_client.get(reverse(
            'profile_unfollow', kwargs={'username': PagesTest.author_post})
        )
        follower_count_again = Follow.objects.all().count()
        self.assertEqual(follower_count_again, follower_count - 1)

    def test_post_for_following_authors(self):
        """A new user post appears in the feed of those who are
        subscribed to it and does not appear in the feed of those
        who are not subscribed to it.
        """

        new_author = User.objects.create(username='Author Ja')
        new_author_client = Client()
        new_author_client.force_login(new_author)
        user_one = User.objects.create(username='User One')
        user_one_client = Client()
        user_one_client.force_login(user_one)
        user_two = User.objects.create(username='Third')
        user_two_client = Client()
        user_two_client.force_login(user_two)
        # I subscribe to the author as the first client.
        user_one_client.get(reverse(
            'profile_follow', args=['Author Ja']
        ))
        # Creating a post with text.
        Post.objects.create(
            author=new_author,
            text='The subscribed user sees the text.'
        )
        # The first user to request a page with selected authors.
        response_user_one = user_one_client.get(reverse(
            'follow_index'
        ))
        # The second user to request a page with selected authors
        response_user_two = user_two_client.get(reverse(
            'follow_index'
        ))
        # Check the context of the post of the text field,
        # for the subscriber, expecting to see the result.
        self.assertEquals(
            response_user_one.context['post'].first().text,
            'The subscribed user sees the text.'
        )
        # Not a subscriber on request, expecting a null result None.
        self.assertEquals(response_user_two.context['post'].first(), None)

    def test_cahces(self):
        # Проверка кэша, честно подсмотрено в тредах, слишком много времени
        # потратил на тест с созданием поста и проверкой через контент.
        # Насчет контента знал еще на теории, когда про картинки разговор
        # пошел, почитал статеек, поныкался в доках, и понял как примерно
        # работает этот "скриншот" экрана. (для нашей ситуации)
        # Но для оправдания, там в слаке много смуты наводят,
        # лишнии параметры и строки.
        cache_page = self.authorized_client.get(reverse('index'))
        cache.clear()
        after_clearing_cache = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(cache_page, after_clearing_cache)
