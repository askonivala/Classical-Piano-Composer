# Classical Piano Composer

This project allows you to train a neural network to generate midi music files that make use of a single instrument.

## Requirements

* Python 3.x
* Installing the following packages using pip:
	* Music21
	* Keras
	* Tensorflow
	* h5py

## Training

To train the network you run **lstm.py**.

E.g.

```
python lstm.py
```

The network will use every midi file in ./midi_songs to train the network. The midi files should only contain a single instrument to get the most out of the 
training. The preprocessing tries to transpose all source files to C, but it does not distinguish between manor and minor keys.

**NOTE**: You can stop the training process at any point in time and the weights from the latest 10th epoch with lower loss value will be available for text 
generation purposes.

## Continue training

To continue training you run **continue.py <weights.hdf5>**. Please note that **data/notes** file have to stay identical in order to continue training. You 
should backup this file together with the model.

## Generating music

Once you have trained the network you can generate midi file using **predict.py <weights.hdf5>**.

E.g.

```
python predict.py weights.hdf5
```
