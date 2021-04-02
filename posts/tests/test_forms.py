from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_author = User.objects.create_user(username='AuthorPost')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user_author)

        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            group=cls.group,
            author=cls.user_author,
        )

    def setUp(self):
        """Authorized users have access to the page with the model."""

        self.user = User.objects.create_user(username='Tester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_new_post(self):
        """Check that after creating a post,
        the number of posts has changed,
        and check the statute code.
        """

        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост для проверки count',
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertNotEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)

    def test_post_edit_form(self):
        """Make sure that when you edit a post through the form on the
        post edit page, the corresponding record in the database is changed.
        """

        post_count = Post.objects.count()
        form_data = {
            'text': 'Проверить изменение поста',
            'group': PostFormTest.group.id,
        }
        response = PostFormTest.author_client.post(reverse(
            'post_edit',
            kwargs={
                'username': PostFormTest.post.author,
                'post_id': PostFormTest.post.id
            }),
            data=form_data,
            follow=False,
        )
        self.assertRedirects(response, reverse(
            'post',
            kwargs={
                'username': PostFormTest.post.author,
                'post_id': PostFormTest.post.id
            }))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=PostFormTest.group.id
            ).exists()
        )
