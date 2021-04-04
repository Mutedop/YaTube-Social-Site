from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class YatubeUrlTests(TestCase):
    """Tests of addresses, names and their accessibility to users.
     Checking templates, redirects.
     """

    @classmethod
    def setUpClass(cls):
        """Installation class for YatubeUrlTests.
         Create a database, posts, groups and possibly the author.
        """

        super().setUpClass()
        cls.author_post = User.objects.create_user(username='AuthorPost')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author_post)
        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            group=cls.group,
            author=cls.author_post,
        )

    def setUp(self):
        """Additional data setting, for tests YatubeUrlTests.
        Set names and templates for posts.url. Create users.
        """

        self.guest_client = Client()
        self.user = User.objects.create_user(username='authUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.templates_url_names = {
            'new.html': '/new/',
            'post.html': (f'/{YatubeUrlTests.post.author}/'
                          f'{YatubeUrlTests.post.id}/'),
            'index.html': '/',
            'group.html': f'/group/{YatubeUrlTests.group.slug}/',
            'profile.html': f'/{YatubeUrlTests.post.author}/'
        }

    def test_urls_status_code(self):
        """Check the availability of pages for an authorized user."""

        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """The URL uses the matching pattern."""

        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_redirect_anonymous_on_login(self):
        """The page /new/ will redirect the anonymous
        user to the login page.
        """

        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_url_post_edit_redirect_guest_on_post(self):
        """The page <username>/<post_id>/edit/ will redirect
        the anonymous user to the login page.
        """

        response = self.guest_client.get(
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{YatubeUrlTests.post.author}/'
            f'{YatubeUrlTests.post.id}/edit/'
        )

    def test_url_post_edit_redirect_authorized_client_on_post(self):
        """Correctness of work <username>/<post_id>/edit/ for the
        authorized user of the author of the post.
        """

        response = self.authorized_client.get(
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/'
        )

    def test_url_post_edit_available_for_author(self):
        """The correctness of the page, the expected template for
        <username>/<post_id>/edit/ work for the authorized user
        of the author of the post.
        """

        response = YatubeUrlTests.author_client.get(
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/edit/',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'new.html')

    def test_anonim_redirect_to_the_login(self):
        """The comment page will redirect the anonymous user
        to the login page.
        """

        response = self.guest_client.get(
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{YatubeUrlTests.post.author}/'
            f'{YatubeUrlTests.post.id}/comment/'
        )

    def test_guest_comment_post(self):
        """An unauthorized user will try to comment on the post."""

        response = self.guest_client.post(
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/comment/',
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{YatubeUrlTests.post.author}/'
            f'{YatubeUrlTests.post.id}/comment/'
        )

    def test_comments_auth_user(self):
        """An authorized user can comment on posts."""

        response = YatubeUrlTests.author_client.get(
            f'/{YatubeUrlTests.post.author}/{YatubeUrlTests.post.id}/comment/',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
