""" This module continues previous training session """

import sys
import glob
import pickle
import numpy
from music21 import converter, instrument, note, chord
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import BatchNormalization
from keras.layers import Activation
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint
from keras.models import load_model

if len(sys.argv) < 2:
    print("Please provide model name as an argument: <python predict.py model.hdf5>")
    sys.exit(0)
else:
    model_path = sys.argv[1]

def train_network():
    """ Train a Neural Network to generate music """
    print("Loading notes")
    with open('data/notes', 'rb') as filepath:
        notes = pickle.load(filepath)

    # get amount of pitch names
    n_vocab = len(set(notes))
    print("Size of vocab: %s" % n_vocab)

    print("Preparing sequences")
    network_input, network_output = prepare_sequences(notes, n_vocab)

    print("Loading network")
    model = load_network()

    train(model, network_input, network_output)

def get_notes():
    """ Get all the notes and chords from the midi files in the ./midi_songs directory """
    notes = []

    count = 0
    for file in glob.glob("midi_songs/*.mid"):
        midi = converter.parse(file)

        count += 1
        print("[%3d] Parsing %s" % (count, file))

        notes_to_parse = None

        try: # file has instrument parts
            s2 = instrument.partitionByInstrument(midi)
            notes_to_parse = s2.parts[0].recurse() 
        except: # file has notes in a flat structure
            notes_to_parse = midi.flat.notes

        for element in notes_to_parse:
            if isinstance(element, note.Note):
                notes.append(str(element.pitch))
            elif isinstance(element, chord.Chord):
                notes.append('.'.join(str(n) for n in element.normalOrder))

    with open('data/notes', 'wb') as filepath:
        pickle.dump(notes, filepath)

    return notes

def prepare_sequences(notes, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    sequence_length = 25

    # get all pitch names
    pitchnames = sorted(set(item for item in notes))

     # create a dictionary to map pitches to integers
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    network_input = []
    network_output = []

    # create input sequences and the corresponding outputs
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
        network_output.append(note_to_int[sequence_out])

    n_patterns = len(network_input)

    # reshape the input into a format compatible with LSTM layers
    network_input = numpy.reshape(network_input, (n_patterns, sequence_length, 1))
    # normalize input
    network_input = network_input / float(n_vocab)

    network_output = np_utils.to_categorical(network_output)

    return (network_input, network_output)

def load_network():
    """ load saved network """
    #model = load_model("weights-improvement-179-0.0358-bigger.hdf5")
    model = load_model(model_path)
    return model

def train(model, network_input, network_output):
    """ train the neural network """
    filepath = "weights-improvement-{epoch:02d}-{loss:.4f}-bigger.hdf5"
    checkpoint = ModelCheckpoint(
        filepath,
        monitor='loss',
        verbose=0,
        save_best_only=True,
        period = 10,
        mode='min'
    )
    callbacks_list = [checkpoint]

    model.fit(network_input, network_output, epochs=1000, batch_size=64, callbacks=callbacks_list)

if __name__ == '__main__':
    train_network()
