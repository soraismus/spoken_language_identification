import time
import re

import numpy as np

import matplotlib.pyplot as plt

from sklearn import preprocessing
from sklearn.metrics import classification_report

from keras.models import Model, load_model
from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten
from keras.layers import Dropout, Input, BatchNormalization
from keras.optimizers import Nadam
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import np_utils

in_dim = (192,192,1)
out_dim = 3

def load_data(label_binarizer, file, skip_augmentation=False):
    bundle = np.load(file)

    metadata = bundle['labels']
    features = bundle['features']

    if skip_augmentation:

        # filename without augmentation
        pattern = re.compile("^.+fragment\d+$")

        mask = []
        for info in metadata:
            filename = info[2]
            if pattern.match(filename):
                mask.append(True)
            else:
                mask.append(False)

        metadata = metadata[mask]
        features = features[mask]

    labels = label_binarizer.transform(metadata[:, 0])

    features = features.reshape((len(features), 192, 192, 1))
    features = np.divide(features, 255.)

    print("[{file}] labels: {labels}, features: {features} (max: {max}, min: {min})".format(
        file=file, labels=labels.shape, features=features.shape, 
        max=np.max(features), min=np.min(features)
    ))

    image = features[0, :, :, 0]
    plt.imshow(image)
    plt.savefig(file + '.png', bbox_inches='tight')

    assert len(metadata) == len(labels)
    assert len(metadata) == len(features)

    return (labels, features, metadata)


def create_model(skip_augmentation):
    label_binarizer = preprocessing.LabelBinarizer()
    label_binarizer.fit(['en', 'de', 'es'])
    print(label_binarizer.classes_)

    start = time.time()
    train_labels, train_features, train_metadata = load_data(label_binarizer, 'train.npz', skip_augmentation=skip_augmentation)
    valid_labels, valid_features, valid_metadata = load_data(label_binarizer, 'valid.npz')
    test_labels, test_features, test_metadata = load_data(label_binarizer, 'test.npz')
    print("Loaded data in [s]: ", time.time() - start)


    i = Input(shape=in_dim)
    m = Conv2D(1, (3, 3), activation='elu', padding='same')(i)
    m = MaxPooling2D()(m)
    # m = Conv2D(16, (3, 3), activation='elu', padding='same')(i)
    # m = MaxPooling2D()(m)
    # m = Conv2D(32, (3, 3), activation='elu', padding='same')(m)
    # m = MaxPooling2D()(m)
    # m = Conv2D(64, (3, 3), activation='elu', padding='same')(m)
    # m = MaxPooling2D()(m)
    # m = Conv2D(128, (3, 3), activation='elu', padding='same')(m)
    # m = MaxPooling2D()(m)
    # m = Conv2D(256, (3, 3), activation='elu', padding='same')(m)
    # m = MaxPooling2D()(m)
    m = Flatten()(m)
    m = Dense(1, activation='elu')(m)
    # m = Dense(512, activation='elu')(m)
    # m = Dropout(0.5)(m)
    o = Dense(out_dim, activation='softmax')(m)

    model = Model(inputs=i, outputs=o)
    model.summary()

    model.compile(loss='categorical_crossentropy', optimizer=Nadam(lr=1e-4), metrics=['accuracy'])
    model.fit(train_features, train_labels, epochs=3, verbose=1, validation_data=(valid_features, valid_labels))

    model.save('language.h5')

    probabilities = model.predict(valid_features, batch_size=32, verbose=1)
    expected = np.argmax(valid_labels, axis=1)
    actual = np.argmax(probabilities, axis=1)

    print("## Validation set\n")
    print(classification_report(expected, actual, target_names=label_binarizer.classes_))

    probabilities = model.predict(test_features, batch_size=32, verbose=1)
    expected = np.argmax(test_labels, axis=1)
    actual = np.argmax(probabilities, axis=1)

    print("## Test set\n")
    print(classification_report(expected, actual, target_names=label_binarizer.classes_))


if __name__ == "__main__":
    start = time.time()

    create_model(skip_augmentation=False)

    print("Generated model in [s]: ", time.time() - start)
