#!/usr/bin/env python
from mrjob.job import MRJob
from mrjob.step import MRStep
import mrjob
from mrjob.protocol import RawValueProtocol, RawProtocol, JSONProtocol, UltraJSONProtocol, StandardJSONProtocol, BytesValueProtocol, BytesProtocol, TextProtocol, PickleProtocol, PickleValueProtocol


class SharesJob(MRJob):

    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = RawProtocol


    def mapper(self, _, line):
        tokens = line.split(' ')
        relation = int(tokens[0][1:])
        attributeValues = tokens[1:]
        for attrValue in attributeValues:
            yield str(relation), attrValue

    def dummy_reducer(self, bucket, values):
        self.increment_counter('group', 'reducers raised', 1)
        count = 0
        for v in values:
            count += 1
        yield bucket, count

    def steps(self):
        return [
            MRStep(
                # mapper_init=self.mapper_init,
                   mapper=self.mapper,
#                    combiner=self.combiner_count_words,
                   # reducer=self.hashReducer,
#                     reducer=self.countReducer
#                    reducer=self.dummy_reducer
                  )
            ]

if __name__ == '__main__':
    SharesJob.run()
