#!/usr/bin/python
# -*- coding: utf-8 -*-

# data type ------------------------------------

# Structure of the number of occurrences of each number, the calculated encoded bit string, and information on the combined part
import array


class HUFFMAN_NODE:
    def __init__(self):
        self.weight = 0 # Number of occurrences (sum of the number of occurrences in combined data)
        self.bitNum = 0 # Number of bits in the compressed bit string (not used in combined data)
        self.bitArray = array.array("I", [0] * 32) # [32] ; # Compressed bit array (not used in combined data)
        self.index = 0 # Reference index assigned to the join data ( 0 or 1 )
        self.parentNode = -1 # Index of the element array of the combined data that this data belongs to
        self.childNode = [
            0,
            0,
        ] # [2] # The element array index of the two elements that this data combines (or -1 for both if not combined data).

    def __repr__(self) -> str:
        return f"""HUFFMAN_NODE
|- weight = {self.weight}
|- bitNum = {self.bitNum}
|- bitArray = {len(self.bitArray)}
|- index = {self.index}
|- parentNode = {self.parentNode}
|- childNode = {self.childNode}
"""


# Data structure for bitwise input/output
class BIT_STREAM:
    def __init__(self):
        self.buffer = array.array("B", [])
        self._bytes = array.array("Q", [])
        self.bits = None

    def __repr__(self) -> str:
        return f"""
BitStream.Buffer - {self.buffer.hex()[:20]}
BitStream.Bytes - {self._bytes}
BitStream.Bits - {self.bits}
"""


#code -----------------------------------------

# Initialize bitwise I/O
def bitStream_Init(bitStream: BIT_STREAM, buffer, isRead: bool) -> BIT_STREAM:
    bitStream.buffer = buffer
    bitStream._bytes = 0
    bitStream.bits = 0
    if not isRead:
        bitStream.buffer[0] = 0

    return bitStream


# Write a bitwise number
def bitStream_Write(bitStream: BIT_STREAM, bitNum, outputData) -> BIT_STREAM:
    for i in range(bitNum):
        bitStream.buffer[bitStream._bytes] |= (
            (outputData >> (bitNum - 1 - i)) & 1
        ) << (7 - bitStream.bits)
        bitStream.bits += 1
        if bitStream.bits == 8:
            bitStream._bytes += 1
            bitStream.bits = 0
            bitStream.buffer[bitStream._bytes] = 0
    return bitStream


# Read a bitwise number
def bitStream_Read(bitStream: BIT_STREAM, bitNum) -> int:
    result = 0
    for i in range(bitNum):
        result = result | (
            ((bitStream.buffer[bitStream._bytes] >> (7 - bitStream.bits)) & 1)
        ) << (bitNum - 1 - i)
        # print(f"\t{result=}")
        bitStream.bits += 1
        if bitStream.bits == 8:
            bitStream._bytes += 1
            # print(f"\t{bitStream._bytes=}")
            bitStream.bits = 0
    # print("bitStream_Read ########################################### ##")
    return result


# Get the number of bits in a given number
def bitStream_GetBitNum(data):
    for i in range(1, 64):
        if data < (1 << i):
            return i
    return i


# Get the size (number of bytes) of the input/output data in bits
def bitStream_GetBytes(bitStream: BIT_STREAM) -> int:
    if bitStream.bits != 0:
        bitStream._bytes += 1
    return bitStream._bytes


# Compress data
#
# Return value: Size after compression. 0 is an error. If Dest is set to NULL, the size required to store the compressed data is returned.
def huffman_Encode(src, srcSize, dest=None) -> tuple:
    # print("Huffman_Encode()")
    # Combined data and numeric data, 0 to 255 is numeric data
    # (The number of combined data and the number of types of data to be compressed always equals "number of types + (number of types - 1)".
    # If you think "Is that really true?", look at the number of connected parts of A, B, C, D, and E in the explanation of Huffman compression.
    # Count them, there should be four types, one less bond than the five.
    # When there are 6 types, there are 5 combinations, and when there are 256 types, there are 255 combinations.)

    # HUFFMAN_NODE Node[256 + 255]
    node = [HUFFMAN_NODE() for _ in range(256 + 255)]

    # Since addresses cannot be manipulated with a void pointer, use an unsigned char pointer.
    srcPoint = src

    # Calculate the compressed bit string for each number
    if True:
        # print("\tBlock 1")
        # Initialize the numerical data
        for i in range(256):
            node[i].weight = 0 # The number of occurrences will be calculated later, so initialize it to 0
            node[i].childNode[0] = -1 # Set -1 since numeric data is the end point
            node[i].childNode[1] = -1 # Set -1 since numeric data is the end point
            node[i].parentNode = -1 # Set to -1 since it's not yet bound to any element

        # Count the occurrences of each number
        for i in range(srcSize):
            node[srcPoint[i]].weight += 1

        # Convert the number of occurrences to a ratio between 0 and 65535
        for i in range(256):
            node[i].weight = int(node[i].weight * 0xFFFF / srcSize)

        # Connect numerical data with few occurrences or combined data
        # Create a new join data, connect all elements and repeat until only one is left
        dataNum = 256 # Number of remaining elements
        nodeNum = 256 # The index of the element array of the next newly created joined data
        while dataNum > 1:
            if True:
                # Find the two elements with the lowest occurrence count
                minNode1 = -1
                minNode2 = -1

                # Loop until all remaining elements have been examined
                nodeIndex = 0
                i = 0
                while (
                    i < dataNum
                ): # "for i in range(dataNum)" would increment i even if we continue, so we use while to increment i ourselves
                    # If it is already combined with some other element, it is excluded.
                    if node[nodeIndex].parentNode != -1:
                        nodeIndex += 1
                        continue

                    i += 1

                    # You haven't set a valid element yet, or you have a higher occurrence number.
                    # Update if fewer elements are found
                    if minNode1 == -1 or node[minNode1].weight > node[nodeIndex].weight:
                        # This was thought to be the lowest number of occurrences to date.
                        # Element is demoted to second place
                        minNode2 = minNode1
                        # Save the element array index of the new first element
                        minNode1 = nodeIndex
                    else:
                        # It may have more occurrences than the first one, but it may have less occurrences than the second one.
                        # It may be small, so check it (or the second most common number)
                        # Set even if few elements are not set)
                        if (
                            minNode2 == -1
                            or node[minNode2].weight > node[nodeIndex].weight
                        ):
                            minNode2 = nodeIndex
                    nodeIndex += 1

            # Join two elements to create a new element (combined data)
            # new_node = HUFFMAN_NODE()
            # node[i] = new_node

            node[nodeNum].parentNode = -1 # The new data is obviously not connected to anything yet, so -1
            node[nodeNum].weight = (
                node[minNode1].weight + node[minNode2].weight
            ) # Set the occurrence value to the sum of the two numbers
            node[nodeNum].childNode = (
                minNode1,
                minNode2,
            ) # If you choose 0 at this join, it will connect to the element with the least number of occurrences.
            # node[nodeNum].childNode[0] = minNode1 # If you choose 1 at this join, it will connect to the element with the second lowest occurrence number.
            # node[nodeNum].childNode[1] = minNode2 # If you choose 1 at this join, it will connect to the element with the second lowest occurrence number.

            # Set the two combined elements to what values ​​they were assigned
            node[minNode1].index = 0 # The element with the least number of occurrences is 0
            node[minNode2].index = 1 # The element with the second lowest occurrence is number 1

            # Set the two combined elements to the array index of the combined data that combined them
            node[minNode1].parentNode = nodeNum
            node[minNode2].parentNode = nodeNum

            # Increase the number of elements by one
            nodeNum += 1

            # The number of remaining elements is increased by one because one new element was added.
            # The two elements are combined and are no longer subject to the search.
            # Result 1 - 2 = -1
            dataNum -= 1

    if True:
        # print("\tBlock 1.2")
        # Figure out the compressed bit sequence for each number
        tempBitArray = bytearray([0] * 32)

        # Repeat for each type of numeric data
        for i in range(256):
            # Count the number of bits by tracing the combined data upwards from the numeric data

            # Initialize the number of bits
            node[i].bitNum = 0

            # Preparation for processing to temporarily save the bit string when going back from the numerical data
            tempBitIndex = 0
            tempBitCount = 0
            tempBitArray[tempBitIndex] = 0

            # Keep counting as long as it is connected to something (the top is not connected to anything, so we know it is the end point)
            nodeIndex = i
            while node[nodeIndex].parentNode != -1:
                # Since there are eight bits per array element,
                # If 8 have already been saved, change the save destination to the next array element
                if tempBitCount == 8:
                    tempBitCount = 0
                    tempBitIndex += 1
                    tempBitArray[tempBitIndex] = 0

                # Shift the data one bit to the left so that the new information does not overwrite the old data.
                tempBitArray[tempBitIndex] <<= 1

                # Write the index assigned to the combined data in the least significant bit (the rightmost bit)
                # TempBitArray[TempBitIndex] |= (unsigned char)Node[NodeIndex].Index
                tempBitArray[tempBitIndex] |= (
                    node[nodeIndex].index % 256
                ) # % 256 might be unnecessary?

                # Increase the number of saved bits
                tempBitCount += 1

                # Increase the number of bits
                node[i].bitNum += 1

                nodeIndex = node[nodeIndex].parentNode

            # The data stored in TempBitArray is the numerical data, then the combined data towards the top.
            # This is the bit string when going back up, so if you don't turn it upside down, it will be the compressed bit
            # Cannot be used as an array (when expanding, it is not possible to trace from the top bound data to the numeric data)
            # It is not possible to do this, so the order is reversed and stored in the bit string buffer in the numeric data.

            bitCount = 0
            bitIndex = 0

            # Initialize the first buffer
            # (All are written using logical OR, so they start out as 1
            # Even if you write a 0 to a bit, it will remain 1.
            node[i].bitArray[bitIndex] = 0

            # Go back to the beginning of the temporarily saved bit string
            while tempBitIndex >= 0:
                # The number of bits written is 8 bits that fit into one array element
                # If reached, move on to the next array element
                if bitCount == 8:
                    bitCount = 0
                    bitIndex += 1
                    node[i].bitArray[bitIndex] = 0

                # Write 1 bit to a bit address that has nothing written yet
                node[i].bitArray[bitIndex] |= (
                    (tempBitArray[tempBitIndex] & 1) << bitCount
                ) % 256 # % 256 might be unnecessary?

                # The bit that has already been written is no longer needed, so write the next bit.
                # Shift one bit right so that it can be written
                tempBitArray[tempBitIndex] >>= 1

                # 1 bit has been written, so the number of remaining bits is reduced by 1
                tempBitCount -= 1

                # If the current source array element is not being written to
                # When there is no more bit information, move on to the next array element
                if tempBitCount == 0:
                    tempBitIndex -= 1
                    tempBitCount = 8

                # Increase the number of written bits
                bitCount += 1

    # Conversion process
    if True:
        # print("\tBlock 2")
        # Set the address to store the compressed data
        # (The compressed data body contains the original size, the compressed size, the number of occurrences of each number, etc.
        # Store after the data area to be stored)
        pressData = bytearray(dest)

        # Initialize the reference address of the data to be compressed
        srcSizeCounter = 0

        # Initialize the reference address of the compressed data
        pressSizeCounter = 0

        # Initialize the compressed bit data counter
        pressBitCounter = 0

        # Initialize the first byte of compressed data
        if dest is not None:
            # pressData[pressSizeCounter] = 0
            pressData.append(0)

        # Loop until all data to be compressed is converted to compressed bit strings
        # for( srcSizeCounter = 0 ; srcSizeCounter < srcSize ; srcSizeCounter ++ )
        while srcSizeCounter < srcSize:

            # Get the index of the numeric data to be saved
            nodeIndex = srcPoint[srcSizeCounter]

            # Output the compressed bit string of the specified numeric data

            # Initialize the index of the referenced array
            bitIndex = 0

            # Initialize the number of output bits in the array elements
            bitNum = 0

            # Set the first bit string to be written
            bitData = node[nodeIndex].bitArray[0]

            # Loop until all bits are output
            bitCounter = 0
            while bitCounter < node[nodeIndex].bitNum:
                # If the number of bits written is 8, move on to the next array element
                if pressBitCounter == 8:
                    pressSizeCounter += 1
                    if dest is not None:
                        # pressData[pressSizeCounter] = 0
                        pressData.append(0)

                    pressBitCounter = 0

                # If the number of bits written out is 8, move on to the next array element
                if bitNum == 8:
                    bitIndex += 1
                    bitData = node[nodeIndex].bitArray[bitIndex]
                    bitNum = 0

                # Write 1 bit to a bit address that has nothing written yet
                if dest is not None:
                    pressData[pressSizeCounter] |= (
                        (bitData & 1) << pressBitCounter
                    ) % 256 # % 256 might be unnecessary?

                # Increase the number of written bits
                pressBitCounter += 1

                # To make the next bit written the least significant bit (the rightmost bit)
                # Shift right 1 bit
                bitData >>= 1

                # Increase the number of bits written
                bitNum += 1

                bitCounter += 1

            srcSizeCounter += 1

        # Add the size of the last byte
        pressSizeCounter += 1

    dest = pressData # Because in c++ it's a pointer or something, I don't know C

    # Save compressed data information
    if True:
        # print("\tBlock 3")
        # u8 HeadBuffer[ 256 * 2 + 32 ]
        headBuffer = array.array("B", [0] * (256 * 2 + 32))

        # s32 WeightSaveData[ 256 ]
        weightSaveData = [0] * 256

        bitStream = BIT_STREAM()
        bitStream = bitStream_Init(bitStream, headBuffer, False)

        # Set the size of the original data
        bitNum = bitStream_GetBitNum(srcSize)

        if bitNum > 0:
            bitNum -= 1
        bitStream = bitStream_Write(bitStream, 6, bitNum)
        bitStream = bitStream_Write(bitStream, bitNum + 1, srcSize)
        # Set the size of the compressed data
        bitNum = bitStream_GetBitNum(pressSizeCounter)
        bitStream = bitStream_Write(bitStream, 6, bitNum)
        bitStream = bitStream_Write(bitStream, bitNum + 1, pressSizeCounter)

        # Save the difference in the occurrence rate of each value
        weightSaveData[0] = node[0].weight
        for i in range(1, 256):
            weightSaveData[i] = node[i].weight - node[i - 1].weight

        for i in range(256):
            minus = True

            if weightSaveData[i] < 0:
                outputNum = -weightSaveData[i]
                minus = True
            else:
                outputNum = weightSaveData[i]
                minus = False

            bitNum = int((bitStream_GetBitNum(outputNum) + 1) / 2)
            if bitNum > 0:
                bitNum -= 1

            bitStream = bitStream_Write(bitStream, 3, bitNum)
            bitStream = bitStream_Write(bitStream, 1, int(minus))
            bitStream = bitStream_Write(bitStream, (bitNum + 1) * 2, outputNum)

        # Get the header size
        headBuffer = (
            bitStream.buffer
        ) # Stupid C and it's pointers and references and whatnot
        headSize = bitStream_GetBytes(bitStream)

        total = pressSizeCounter + headSize

        temp = bytearray([0] * total)

        # Copy the compressed data information to the compressed data
        if dest is not None:
            # Move by the header
            #
            # Maybe this is just headBuffer+dest
            # Maybe this is just headBuffer.axtend(dest)
            #
            j = pressSizeCounter - 1
            while j >= 0:
                # print(f"ON {headSize+j} -> {dest[j]}")
                # ( ( u8 * )Dest )[ HeadSize + j ] = ( ( u8 * )Dest )[ j ]
                # dest[headSize+j] = dest[j]
                temp[headSize + j] = dest[j]
                temp[j] = dest[j]
                if j == 0:
                    break
                j -= 1

            # Write the header
            # memcpy( Dest, HeadBuffer, ( size_t )HeadSize )
            """
            mayor = max(len(temp),len(temp[:headSize]),len(headBuffer))
            #print(f"idx\ttemp{len(temp)}\t\ttemp2{len(temp[:headSize])}\thead{len(headBuffer)}")
            for x in range(mayor):
                try:
                    a = temp[x]
                except IndexError:
                    a = ' '
                try:
                    b = temp[:headSize][x]
                except IndexError:
                    b = ' '
                try:
                    c = headBuffer[x]
                except IndexError:
                    c = ' '

                #print(f"{x}\t{a}\t\t{b}\t\t{c}")
            """

            # for i in range(headSize):
            # headBuffer[i+headSize] = temp[i]

            # dest = headBuffer[:headSize] + temp[:headSize]

            for idx, x in enumerate(headBuffer[:headSize]):
                temp[idx] = x

            dest = temp

    # Return the compressed size
    return (dest, pressSizeCounter + headSize)


def huffman_Decode(press, dest=None) -> tuple:
    # Combined data and numeric data, 0 to 255 is numeric data
    node = [HUFFMAN_NODE() for _ in range(256 + 255)]

    # u16Weight[ 256 ] ;
    weight = array.array("H", [0] * 256)

    # Since addresses cannot be manipulated with a void pointer, use an unsigned char pointer.
    pressPoint = press
    destPoint = dest

    # Get compressed data information
    if True:
        bitStream = BIT_STREAM()
        bitStream = bitStream_Init(bitStream, pressPoint, True)

        originalSize = bitStream_Read(
            bitStream, (bitStream_Read(bitStream, 6) + 1) % 256
        )
        pressSize = bitStream_Read(bitStream, (bitStream_Read(bitStream, 6) + 1) % 256)

        # Recover the frequency table
        bitNum = (bitStream_Read(bitStream, 3) + 1) * 2
        minus = bitStream_Read(bitStream, 1)
        saveData = bitStream_Read(bitStream, bitNum)
        weight[0] = saveData
        for i in range(1, 256):
            bitNum = (bitStream_Read(bitStream, 3) + 1) * 2
            minus = bitStream_Read(bitStream, 1)
            saveData = bitStream_Read(bitStream, bitNum)
            if minus == 1:
                weight[i] = (weight[i - 1] - saveData) % 2**16
            else:
                weight[i] = (weight[i - 1] + saveData) % 2**16

        # Get the header size
        headSize = bitStream_GetBytes(bitStream)

    # If Dest is NULL, returns the size of the decompressed data.
    if dest is None:
        return originalSize

    # Get the size of the decompressed data
    destSize = originalSize

    # print(f"{originalSize=}")
    # print(f"{destSize=}")

    # Build the combined data for each number
    if True:
        # Initialize the numerical data
        for i in range(256 + 255):
            try:
                _weight = weight[i]
            except IndexError:
                _weight = 0
            node[i].weight = _weight # The number of occurrences is copied from the saved data
            node[i].childNode[0] = -1 # Set -1 since numeric data is the end point
            node[i].childNode[1] = -1 # Set -1 since numeric data is the end point
            node[i].parentNode = -1 # Set to -1 since it's not yet bound to any element

        # Connect numerical data with few occurrences or combined data
        # Create a new join data, connect all elements and repeat until only one is left
        # (This is the same code as when compressing)
        dataNum = 256 # Number of remaining elements
        nodeNum = 256 # The index of the element array of the next newly created joined data
        while dataNum > 1:
            # Find the two elements with the lowest occurrence count
            minNode1 = -1
            minNode2 = -1

            # Loop until all remaining elements have been examined
            nodeIndex = 0
            i = 0
            while i < dataNum:
                if node[nodeIndex].parentNode != -1:
                    nodeIndex += 1
                    continue

                i += 1

                # You haven't set a valid element yet, or you have a higher occurrence number.
                # Update if fewer elements are found
                if minNode1 == -1 or node[minNode1].weight > node[nodeIndex].weight:
                    # This was thought to be the lowest number of occurrences to date.
                    # Element is demoted to second place
                    minNode2 = minNode1

                    # Save the element array index of the new first element
                    minNode1 = nodeIndex
                else:
                    # It may have more occurrences than the first one, but it may have less occurrences than the second one.
                    # It may be small, so check it (or the second most common number)
                    # Set even if few elements are not set)
                    if minNode2 == -1 or node[minNode2].weight > node[nodeIndex].weight:
                        minNode2 = nodeIndex
                nodeIndex += 1

            # Join two elements to create a new element (combined data)
            node[nodeNum].parentNode = -1 # The new data is obviously not connected to anything yet, so -1
            node[nodeNum].weight = (
                node[minNode1].weight + node[minNode2].weight
            ) # Set the occurrence value to the sum of the two numbers
            node[nodeNum].childNode[0] = minNode1 # If you choose 0 at this connection, it will connect to the element with the least number of occurrences
            node[nodeNum].childNode[1] = minNode2 # If you choose 1 at this join, it will connect to the element with the second lowest occurrence number.

            # Set the two combined elements to what values ​​they were assigned
            node[minNode1].index = 0 # The element with the least number of occurrences is 0
            node[minNode2].index = 1 # The element with the second lowest occurrence is number 1

            # Set the two combined elements to the array index of the combined data that combined them
            node[minNode1].parentNode = nodeNum
            node[minNode2].parentNode = nodeNum

            # Increase the number of elements by one
            nodeNum += 1

            # The number of remaining elements is increased by one because one new element was added.
            # The two elements are combined and are no longer subject to the search.
            # Result 1 - 2 = -1
            dataNum -= 1

        # Figure out the compressed bit sequence for each number
        if True:
            tempBitArray = bytearray([0] * 32)

            # Repeat for each numeric data and combined data
            for i in range(256 + 254):
                # Count the number of bits by tracing the combined data upwards from the numeric data
                # Initialize the number of bits
                node[i].bitNum = 0

                # Preparation for processing to temporarily save the bit string when going back from the numerical data
                tempBitIndex = 0
                tempBitCount = 0
                tempBitArray[tempBitIndex] = 0

                # Keep counting as long as it is connected to something (the top is not connected to anything, so we know it is the end point)
                nodeIndex = i
                while node[nodeIndex].parentNode != -1:
                    # Since there are eight bits per array element,
                    # If 8 have already been saved, change the save destination to the next array element
                    if tempBitCount == 8:
                        tempBitCount = 0
                        tempBitIndex += 1
                        tempBitArray[tempBitIndex] = 0

                    # Shift the data one bit to the left so that the new information does not overwrite the old data.
                    tempBitArray[tempBitIndex] <<= 1

                    # Write the index assigned to the combined data in the least significant bit (the rightmost bit)
                    tempBitArray[tempBitIndex] |= (
                        node[nodeIndex].index % 256
                    ) # % 256 might be unnecessary?

                    # Increase the number of saved bits
                    tempBitCount += 1

                    # Increase the number of bits
                    node[i].bitNum += 1

                    nodeIndex = node[nodeIndex].parentNode

                # The data stored in TempBitArray is the numerical data, then the combined data towards the top.
                # This is the bit string when going back up, so if you don't turn it upside down, it will be the compressed bit
                # Cannot be used as an array (when expanding, it is not possible to trace from the top bound data to the numeric data)
                # It is not possible to do this, so the order is reversed and stored in the bit string buffer in the numeric data.
                bitCount = 0
                bitIndex = 0

                # Initialize the first buffer
                # (All are written using logical OR, so they start out as 1
                # Even if you write a 0 to a bit, it will remain 1.
                node[i].bitArray[bitIndex] = 0

                # Go back to the beginning of the temporarily saved bit string
                while tempBitIndex >= 0:
                    # The number of bits written is 8 bits that fit into one array element
                    # If reached, move on to the next array element
                    if bitCount == 8:
                        bitCount = 0
                        bitIndex += 1
                        node[i].bitArray[bitIndex] = 0

                    # Write 1 bit to a bit address that has nothing written yet
                    node[i].bitArray[bitIndex] |= (
                        tempBitArray[tempBitIndex] & 1
                    ) << bitCount % 256 # % 256 might be unnecessary?
                    # print(f"node[i].bitArray[bitIndex] = {node[i].bitArray[bitIndex]}")

                    # The bit that has already been written is no longer needed, so write the next bit.
                    # Shift one bit right so that it can be written
                    tempBitArray[tempBitIndex] >>= 1

                    # 1 bit has been written, so the number of remaining bits is reduced by 1
                    tempBitCount -= 1

                    # If the current source array element is not being written to
                    # When there is no more bit information, move on to the next array element
                    if tempBitCount == 0:
                        tempBitIndex -= 1
                        tempBitCount = 8

                    # Increase the number of written bits
                    bitCount += 1

    # Decompression process
    if True:
        # unsigned char *PressData ;

        nodeIndexTable = [0] * 512

        # Create a table of which nodes each bit array connects to
        # u16 BitMask[ 9 ]
        bitMask = array.array("H", [0] * 9)

        for i in range(9):
            bitMask[i] = (1 << (i + 1)) - 1

        for i in range(512):
            nodeIndexTable[i] = -1

            # Find a node that matches the bit string
            for j in range(256 + 254):
                bitArray01 = bytearray()

                if node[j].bitNum > 9:
                    continue

                bitArray01 = node[j].bitArray[0] | (node[j].bitArray[1] << 8)
                if (i & bitMask[node[j].bitNum - 1]) == (
                    bitArray01 & bitMask[node[j].bitNum - 1]
                ):
                    nodeIndexTable[i] = j
                    break
        # Set the start address of the compressed data body
        # (The compressed data body contains the original size, the compressed size, the number of occurrences of each number, etc.
        # after the data area to be stored)

        #
        # (unsigned char *) PressPoint
        # u64 HeadSize
        # unsigned long long HeadSize
        #

        # Byte shifting ????

        pressData = pressPoint[headSize:]

        # Initialize the storage address of the decompressed data
        destSizeCounter = 0

        # Initialize the reference address of the compressed data
        pressSizeCounter = 0

        # Initialize the compressed bit data counter
        pressBitCounter = 0

        # Set the first byte of compressed data
        pressBitData = pressData[pressSizeCounter]

        # Repeat the decompression process until the data size reaches the original size

        for destSizeCounter in range(destSize):
            # Search for numerical data from bit string
            # Search for the last 17 bytes of data from the top (because there is a possibility of illegal memory access when trying to read the next-to-last byte)
            if destSizeCounter >= destSize - 17:
                # The top of the combined data is the 510th (counting from 0) where the last combined data is stored.
                # Go down from the top
                nodeIndex = 510
            else:
                # Else use a table
                # If all the bits stored in PressBitData are
                # If the bit data is exhausted,
                # Set bit data
                if pressBitCounter == 8:
                    pressSizeCounter += 1
                    pressBitData = pressData[pressSizeCounter]
                    pressBitCounter = 0

                # Prepare 9 bits of compressed data
                tmp1 = pressData[pressSizeCounter + 1]
                pressBitData = (pressBitData | (tmp1 << (8 - pressBitCounter))) & 0x1FF
                # Find the first join data from the table
                nodeIndex = nodeIndexTable[pressBitData]

                # Advance the compressed data address by the amount used
                pressBitCounter += node[nodeIndex].bitNum
                if pressBitCounter >= 16:
                    pressSizeCounter += 2
                    pressBitCounter -= 16
                    pressBitData = pressData[pressSizeCounter] >> pressBitCounter
                elif pressBitCounter >= 8:
                    pressSizeCounter += 1
                    pressBitCounter -= 8
                    pressBitData = pressData[pressSizeCounter] >> pressBitCounter
                else:
                    pressBitData >>= node[nodeIndex].bitNum

            # Go down the join data until you reach the numeric data
            while nodeIndex > 255:
                # If all the bits stored in PressBitData are
                # If the bit data is exhausted,
                # Set bit data
                if pressBitCounter == 8:
                    pressSizeCounter += 1
                    pressBitData = pressData[pressSizeCounter]
                    pressBitCounter = 0

                # Get 1 bit
                index = pressBitData & 1

                # Shift right by the 1 bit used
                pressBitData >>= 1

                # Increase the number of bits used by one
                pressBitCounter += 1

                # Move to the next element (we don't know yet whether it's bound data or numeric data)
                nodeIndex = node[nodeIndex].childNode[index]

            # Output the numerical data you arrive at
            destPoint[destSizeCounter] = nodeIndex

    dest = destPoint
    # Return the size after decompression
    return (dest, originalSize)


def main():
    source = b"Lorem ipsum dolor sit amet consectetur adipisicing elit. Molestias earum mollitia iure consequatur minima magnam nesciunt, similique dicta quasi ipsam minus aliquid laudantium labore, fuga ad facere alias ea adipisci"
    # with open("test.html", mode="rb") as fp:
    # source = fp.read()

    print(f"Encoding string with length {len(source)}")
    dest = array.array("I", [])
    dest, size = huffman_Encode(source, len(source), dest)
    print(f"Encoded to length {size}")

    originalSize = huffman_Decode(dest, None)

    print(f"We need buffer with length {originalSize}")

    dest_b = array.array("I", [0] * originalSize)
    dest_b, originalSize = huffman_Decode(dest, dest_b)

    print("".join([chr(x) for x in dest_b]))


if __name__ == "__main__":
    main()

