# -*- coding:utf-8 -*-

from beem import Steem
from beem.comment import Comment
from beem.exceptions import ContentDoesNotExistsException

from steem.settings import STEEM_HOST
from steem.markdown import SteemMarkdown
from utils.logging.logger import logger


class SteemComment:

    def __init__(self, comment=None, author_perm=None, url=None):
        self.comment = comment
        self.author_perm = author_perm
        self.url = url

    def get_author_perm(self):
        if self.author_perm is None:
            self.author_perm = "/".join(self.url.split("/")[-2:])
        return self.author_perm

    def get_comment(self):
        if self.comment is None:
            self.comment = Comment(self.get_author_perm())
        return self.comment

    def get_url(self):
        if self.url is None:
            if self.author_perm:
                self.url = u"{}/{}".format(STEEM_HOST, self.author_perm)
            else:
                c = self.get_comment()
                if c.authorperm:
                    self.url = u"{}/{}".format(STEEM_HOST, c.authorperm)
                else:
                    self.url = u"{}/@{}/{}".format(STEEM_HOST, c.author, c.permlink)

        return self.url

    def get_pic_url(self, regex=False, default_img = 'https://cdn.steemitimages.com/DQmNUYttPwL2nEhCGRXSxp3WnEt4W63d9jwYKXLHiPGinPM/image.png'):
        body = self.get_comment().body
        image_url = SteemMarkdown(body).get_top_image(regex)
        if image_url == None:
            image_url = default_img
        return image_url

    def get_text_body(self):
        body = self.get_comment().body
        return SteemMarkdown(body).get_rendered_text()

    def get_compatible_markdown(self):
        body = self.get_comment().body
        return SteemMarkdown(body).get_steem_markdown()

    def get_tags(self):
        c = self.get_comment()
        if c.json_metadata and 'tags' in c.json_metadata:
            return c.json_metadata['tags']
        else:
            self.refresh()
            c = self.get_comment()
            if c.json_metadata and 'tags' in c.json_metadata:
                return c.json_metadata['tags']
        return []

    def has_tag(self, tag):
        return tag in self.get_tags()

    def has_tags(self, tags):
        if not tags or len(tags) == 0:
            return False
        for tag in tags:
            if self.has_tag(tag):
                return True
        return False

    def refresh(self):
        c = self.get_comment()
        try:
            c.refresh()
        except ContentDoesNotExistsException:
            logger.info("Failed when refresh {} with title [{}], which is probably deleted.".format(self.get_url(), c.title))
            return None

        return c

    def log(self):
        c = self.get_comment()
        logger.info("@%s | %s | %s | %s" % (c.author, c.title, self.get_url(), c['created']))

    def is_commented_by(self, account):
        commented_by = [reply['author'] for reply in self.get_comment().get_replies()]
        return account in commented_by

    def is_upvoted_by(self, account):
        voters = self.get_comment().get_curation_rewards()['active_votes'].keys()
        return account in voters

    def is_downvoted_by(self, account):
        has_downvoted = False
        for vote in self.get_comment().get_votes():
            if vote.voter == account and vote.percent < 0:
                has_downvoted = True
        return has_downvoted

    def is_comment(self):
        c = self.get_comment()
        return c["parent_author"] != ''
