from steem.blockchain import Blockchain
from datetime import datetime
from steem.post import Post

class BlockPointer:
    LAST_BLOCK_NUM_FILE = "etc/last_block_num"
    def __init__(self):
        self.last_block = None
        try:
            with open("etc/last_block_num", "r") as f:
                self.last_block = (int(f.read()))
                print('Start from block number %d' % self.last_block)
        except:
            print('First start!')

    def last(self):
        return self.last_block
    def update(self, block_num):
        if not self.last_block or self.last_block < block_num:
            self.last_block = block_num
            with open("etc/last_block_num", "w") as f:
                f.write(str(block_num))

class PostStream:
    LAST_BLOCK_NUM_FILE = "etc/last_block_num"
    blockchain = Blockchain()
    def __init__(self, block_pointer):
        self.bp = block_pointer
        if self.bp.last():
            self.stream = self.blockchain.stream_from(self.bp.last())
        else:
            self.stream = self.blockchain.stream_from()

    def get(self):
        try:
            while True:
                block = next(self.stream)
                self.bp.update(block['block'])
                if block['op'][0] == 'comment':
                    post = block['op'][1]
                    post['block_num'] = block['block']
                    return post
        except:
            print('Failed receiving from the stream')
            raise



#s = blockchain.stream(filter_by=['comment'])


ps = PostStream(BlockPointer())

while True:
    try:
        post = ps.get()
        print(Post(post))
        print("{time} block_num={block_num}".format(time=datetime.now(),block_num=post['block_num']))
    except Exception as e:
        print(e)


