import random
from datetime import datetime, timedelta
from steem import Steem

POSTING_GUARD_TIME = timedelta(seconds=20)

class Performer:

    def __init__(self, config, poster, priv_keys, on_complete):
        self.config = config
        self.poster = poster
        self.on_complete = on_complete
        self.steem = Steem(keys=priv_keys)
        self.last_posting = datetime.now() - POSTING_GUARD_TIME

    def is_busy(self):
        if (datetime.now() - self.last_posting) < POSTING_GUARD_TIME:
            return False
        return True

    def leave_comment(self, post):
        print("ID: %s, %s (%s)" % (post['identifier'], post, post['bot-signal']))
        print ("%s: %s/%s > %s" %(post['root_title'], post['parent_author'], post['author'], post['body']))

        result = True
        try:
            parent_id = "@%s/%s" % (post['parent_author'],post['parent_permlink'])
            body_text = "%s\n%s" % (
                random.choice(self.poster['photo']),
                'Hello @%s! @%s told me you need my help! :D\nThanks for calling me! I am just a tiny guide puppy who is eager to help the KR friends not to be bothred by the spammers. But.... I am not ready yet... :) \n Please check the detail in: https://steemit.com/kr/@asbear/kr-kr' % (
                    post['parent_author'], post['author']
                )
            )
            self.steem.commit.post(
                title='guide puppy',
                body=body_text,
                author=self.poster['account'],
                permlink=None,
                reply_identifier=parent_id,
                json_metadata=None,
                comment_options=None,
                community=None,
                tags=None,
                beneficiaries=None,
                self_vote=False
            )
        except Exception as e:
            print(e)
            result = False
            
        self.on_complete({'result': True,
                'poster': self,
                'post': post})

