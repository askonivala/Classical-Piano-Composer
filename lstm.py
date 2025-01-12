""" This module prepares midi file data and feeds it to the neural
    network for training """
import glob
import pickle
import numpy
#from music21 import converter, instrument, note, chord
from music21 import *
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import CuDNNLSTM
#from keras.layers import LSTM
from keras.layers import BatchNormalization
from keras.layers import Activation
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint

def train_network():
    """ Train a Neural Network to generate music """
    notes = get_notes()
    #print("Loading notes")
    #with open('data/notes', 'rb') as filepath:
    #    notes = pickle.load(filepath)

    # get amount of pitch names
    n_vocab = len(set(notes))
    print("Size of vocab: %s" % n_vocab)

    print("Preparing sequences")
    network_input, network_output = prepare_sequences(notes, n_vocab)

    print("Creating network")
    model = create_network(network_input, n_vocab)

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

        try:
            k = notes_to_parse.analyze('key')
            i = interval.Interval(k.tonic, pitch.Pitch('C'))
            sNew = notes_to_parse.transpose(i)
        except:
            print("Failed to analyze the key.")

        for element in sNew:
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

def create_network(network_input, n_vocab):
    """ create the structure of the neural network """
    size = 3
    model = Sequential()
    model.add(CuDNNLSTM(
        512 * size,
        input_shape=(network_input.shape[1], network_input.shape[2]),
        return_sequences=True
    ))
    model.add(Dropout(0.3))
    model.add(CuDNNLSTM(512 * size, return_sequences=True))
    model.add(Dropout(0.3))
    model.add(CuDNNLSTM(512 * size))
    #model.add(Dense(256))
    #model.add(Dropout(0.3))
    model.add(BatchNormalization())
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adagrad')

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
