from steem import Steem

class Performer:
    def __init__(self, config):
        self.config = config
        self.steem = Steem(
            keys=[self.config.get('private_posting_key'),
                  self.config.get('private_active_key')])

    def leave_comment(self, post):
        print("ID: %s, %s (%s)" % (post.get('identifier'), post, post['bot-signal']))
        print ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))

        self.steem.commit.post(
            title='guide puppy',
            body='Sorry, I am not ready yet!',
            author='krguidedog',
            permlink=None,
            reply_identifier=post.get('identifier'),
            json_metadata=None,
            comment_options=None,
            community=None,
            tags=None,
            beneficiaries=None,
            self_vote=True
        )
