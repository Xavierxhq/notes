# -*- coding: utf-8 -*-
"""

@author: xavier

"""

import sys
import tensorflow as tf
import model
import util
slim = tf.contrib.slim

flags = tf.app.flags

flags.DEFINE_string('logdir', None, 'Log directory of this experiment.')
flags.DEFINE_string('noise', None, 'Noise of this experiment. e.g. 20 means 20%')
FLAGS = flags.FLAGS


def main(_):
    num_samples = 800 # we use 800 samples to test the model trained
    log = FLAGS.logdir
    if not log:
        print('logdir arguement is required! could be [usps|both|steps]')
        exit()
    record_path = './records/usps_28x28_800.record' # record file contains data
    logdir = './hand-written_number/test_' + log
    # this is where we restore the model, meaning we use the trained model
    checkpoint_path = './hand-written_number/trainer_' + log + '' if not FLAGS.noise else ('_noise%s' % FLAGS.noise)

    dataset = util.get_record_dataset(record_path, num_samples=num_samples, image_shape=[28, 28, 1])
    data_provider = slim.dataset_data_provider.DatasetDataProvider(dataset)
    image, label = data_provider.get(['image', 'label'])
    # Data augumentation
    image = tf.image.random_flip_left_right(image)
    inputs, labels = tf.train.batch([image, label], batch_size=num_samples, allow_smaller_final_batch=True)

    # following getting the model
    cls_model = model.Model(is_training=False, num_classes=10)
    preprocessed_inputs = cls_model.preprocess(inputs)
    prediction_dict = cls_model.predict(preprocessed_inputs)
    loss_dict = cls_model.loss(prediction_dict, labels)
    loss = loss_dict['loss']
    postprocessed_dict = cls_model.postprocess(prediction_dict)
    acc = cls_model.accuracy(postprocessed_dict, labels)

    # for output on shell
    loss_op = tf.summary.scalar('loss', loss)
    loss_op = tf.Print(loss_op, [loss], '【TEST %s --Loss】' % log)
    accuracy_op = tf.summary.scalar('accuracy', acc)
    accuracy_op = tf.Print(accuracy_op, [acc], '【TEST %s ++Accuracy】' % log)
    summary_ops = [loss_op, accuracy_op]

    names_to_values, names_to_updates = slim.metrics.aggregate_metric_map({
        'accuracy': slim.metrics.streaming_accuracy(postprocessed_dict['classes'], labels),
        # 'eval/Recall@5': slim.metrics.streaming_recall_at_k(logits, labels, 5),
    })

    checkpoint_path_latest = tf.train.latest_checkpoint(checkpoint_path)
    print(checkpoint_path_latest, 'found.')
    sys.stdout.flush()

    # evaluate the model with data from record file
    tf.train.get_or_create_global_step()
    metric_values = slim.evaluation.evaluation_loop(master='',
                                        checkpoint_dir=checkpoint_path,
                                        logdir=logdir,
                                        num_evals=5,
                                        max_number_of_evaluations=6000,
                                        eval_interval_secs=40,
                                        eval_op=names_to_updates.values(),
                                        summary_op=tf.summary.merge(summary_ops),
                                        final_op=names_to_values)
    names_to_values = dict(zip(names_to_values.keys(), metric_values.values()))
    # content = '%s\t\r\nTEST %s Accuracy: %f\t\r\b\t\r\n' % (checkpoint_path, log, names_to_values['accuracy'])
    # with open(logdir + '/eval.txt', 'ab+') as fp:
    #     fp.write(content.encode())
    # print(content)

if __name__ == '__main__':
    tf.app.run()
