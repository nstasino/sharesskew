import re

from mrjob.job import MRJob
from mrjob.protocol import (BytesProtocol, BytesValueProtocol, JSONProtocol,
                            PickleProtocol, PickleValueProtocol, RawProtocol,
                            RawValueProtocol, StandardJSONProtocol,
                            TextProtocol, UltraJSONProtocol)

WORD_RE = re.compile(r"[\w']+")


class Shares(MRJob):

    #     INPUT_PROTOCOL = RawValueProtocol
    #     INTERNAL_PROTOCOL = PickleProtocol
    #     OUTPUT_PROTOCOL = StandardJSONProtocol

    #     def mapper_init(self):
    #         self.shares = {}
    #         with open(self.options.sharesFile, 'r') as f:
    #             for l in f:
    #                 tokens = l.split('\t')
    #                 self.shares[tokens[0]] = tokens[1]

    def mapper(self, _, line):
        yield line, 1

#     def combiner(self, word, counts):
#         yield word, sum(counts)

#     def reducer(self, word, counts):
#         yield word, sum(counts)


#     def configure_options(self):
#             super(MRWordFreqCount, self).configure_options()
#             self.add_passthrough_option(
#                 '--internal-format', default='json', choices=['pickle', 'json'],
#                 help="Specify the internal format of the job")
#             self.add_file_option('--sharesFile')

#     def internal_protocol(self):
#         if self.options.internal_format == 'json':
#             return StandardJSONProtocol()
#         elif self.options.internal_format == 'pickle':
#             return PickleProtocol()

if __name__ == '__main__':
    MRWordFreqCount.run()
