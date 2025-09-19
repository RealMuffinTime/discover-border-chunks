import anvil
import datetime
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import os.path
from nbt import nbt
from PIL import Image
from os import listdir
from os.path import isfile, join

max_x, min_x, max_z, min_z, size = 0, 0, 0, 0, (0, 0)
world_version, world_name, world_dimension, dbc_path = "", "", "", ""

version = "v0.3.0-pre"

# TODO MCA selects different
# TODO generate differences between worlds
# TODO improve generate pockets hashmap again? earlier in the process?
# TODO shorten borders at the end

# It is recommended to generate chunks data yourself using MCA Selector filters, you can use this one:
# Status = "minecraft:noise" OR Status = "minecraft:surface" OR Status = "minecraft:carvers" OR Status = "minecraft:liquid_carvers" OR Status = "minecraft:features" OR Status = "minecraft:light" OR Status = "minecraft:initialize_light" OR Status = "minecraft:spawn" OR Status = "minecraft:heightmaps" OR Status = "minecraft:full" OR (Status = "minecraft:structure_starts" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:structure_references" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:biomes" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:empty" AND Palette contains "minecraft:bedrock")
# This script can also do it, but it's much slower

# Put your root folder here (parent folder of your worlds)
root = "D:\\Dokumente\\0 minecraft server\\mc.muffintime.tk"

# Put your world versions here (parent folders of your worlds)
world_versions = ["1.16.5", "1.18.2", "1.19.4", "1.20.4", "1.21.1"]

# Put your world base names corresponding to the world version
world_names = ["world", "world", "world", "world", "world"]

# Define whether world save format is vanilla or bukkit corresponding to the world version
world_vanilla = [False, False, False, True, True]


def folders_exists():
    exists = True
    for i in range(len(world_versions)):
        if not exists:
            return False
        exists = os.path.isdir(root + "\\" + world_versions[i] + "\\" + world_names[i])
    return exists


def generate_chunks(region_path):
    print("Generating chunk data.")
    start = datetime.datetime.now()

    chunks_dict = {}

    if os.path.exists(f"{dbc_path}\\chunks_{world_name}_{world_dimension}.csv"):
        print("Found existing data.")
        chunks_dict = read_chunks(f"{dbc_path}\\chunks_{world_name}_{world_dimension}.csv")
    else:
        files = [f for f in listdir(region_path) if isfile(join(region_path, f))]

        print("Regions:", len(files))

        i = 0
        while i < len(files):
            split = files[i].split(".")
            region = anvil.Region.from_file(join(region_path, files[i]))
            print(f"Processing region: {i}/{len(files)}.")
            x = 0
            while x < 32:
                z = 0
                while z < 32:
                    data: nbt.NBTFile = region.chunk_data(x, z)

                    position = [x + int(split[1]) * 32, z + int(split[2]) * 32]

                    if data is not None:

                        try:
                            state = data["Status"]

                        except:
                            state = data["Level"]["Status"]

                        state = str(state)

                        # MCA Selector Filter, underscores and colon must be in ""
                        # Works pretty good on all versions and worlds, but some chunks are not selected
                        # Status = "minecraft:noise" OR Status = "minecraft:surface" OR Status = "minecraft:carvers" OR Status = "minecraft:liquid_carvers" OR Status = "minecraft:features" OR Status = "minecraft:light" OR Status = "minecraft:spawn" OR Status = "minecraft:heightmaps" OR Status = "minecraft:full" OR (Status = "minecraft:structure_starts" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:structure_references" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:biomes" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:empty" AND Palette contains "minecraft:bedrock")

                        if (state == "noise" or state == "surface" or state == "carvers" or state ==
                                "liquid_carvers" or state == "features" or state == "light" or state == "initialize_light" or state ==
                                "spawn" or state == "heightmaps" or state == "full"):
                            chunks_dict.update({str(position): position})
                            pass
                        elif state == "empty" or state == "structure_starts" or state == "structure_references" or state == "biomes":
                            try:
                                appended = False
                                sections = data["sections"]
                                for section in sections:
                                    if appended:
                                        break
                                    for block in section["block_states"]["palette"]:
                                        if appended:
                                            break
                                        if str(block["Name"]) == "minecraft:stone":
                                            chunks_dict.update({str(position): position})
                                            appended = True
                            except:
                                pass
                    z += 1
                x += 1
            i += 1

        write_chunks(f"{dbc_path}\\chunks_{world_name}_{world_dimension}.csv", chunks_dict)

    print(f"Generating took {datetime.datetime.now() - start}.\n")

    generate_size(chunks_dict)
    generate_plot("chunks", chunks_dict)

    return chunks_dict


def generate_size(chunks_data):
    print("Calculating sizes.")
    start = datetime.datetime.now()

    print("Chunks:", len(chunks_data))

    global max_x
    max_x = max(chunks_data[key][0] for key in chunks_data.keys())

    global min_x
    min_x = min(chunks_data[key][0] for key in chunks_data.keys())

    global max_z
    max_z = max(chunks_data[key][1] for key in chunks_data.keys())

    global min_z
    min_z = min(chunks_data[key][1] for key in chunks_data.keys())

    print("Max x pos:", max_x)
    print("Min x pos:", min_x)
    print("Max z pos:", max_z)
    print("Min z pos:", min_z)

    global size
    size = (abs(min_x - max_x) + 1, abs(min_z - max_z) + 1)
    print("Size:", size)
    print(f"Generating sizes took {datetime.datetime.now() - start}.\n")


def generate_edge_chunks(chunks_dict):
    print("Generating edge_chunks.")
    start = datetime.datetime.now()

    readAndWrite = False

    if os.path.exists(f"{dbc_path}\\edge_chunks_{world_name}_{world_dimension}.csv") and readAndWrite:
        print("Found existing data.")
        edge_chunks_dict = read_chunks(f"{dbc_path}\\edge_chunks_{world_name}_{world_dimension}.csv")
    else:
        edge_chunks_dict = {}

        for key in chunks_dict.keys():
            pos_x = chunks_dict[key][0]
            pos_z = chunks_dict[key][1]

            # 0 border, 1 no border
            chunk_info = [0, 0, 0, 0, [-1, -1], [-1, -1], [-1, -1], [-1, -1]]

            # up
            if str([pos_x, pos_z - 1]) in chunks_dict:
                chunk_info[0] = 1

            # right
            if str([pos_x + 1, pos_z]) in chunks_dict:
                chunk_info[1] = 1

            # down
            if str([pos_x, pos_z + 1]) in chunks_dict:
                chunk_info[2] = 1

            # left
            if str([pos_x - 1, pos_z]) in chunks_dict:
                chunk_info[3] = 1

            if chunk_info[0] == 0 or chunk_info[1] == 0 or chunk_info[2] == 0 or chunk_info[3] == 0:
                chunk = chunks_dict[key]
                chunk.extend(chunk_info)
                edge_chunks_dict.update({key: chunk})

        if readAndWrite:
            write_chunks(f"{dbc_path}\\edge_chunks_{world_name}_{world_dimension}.csv", edge_chunks_dict)

    print(f"Generating took {datetime.datetime.now() - start}.\n")

    generate_plot("edge_chunks", edge_chunks_dict)

    return edge_chunks_dict


def generate_borders(edge_chunks_dict):
    print("Generating borders.")
    start = datetime.datetime.now()

    borders_data = []
    chunks = edge_chunks_dict.copy()

    while len(chunks) != 0:

        chunk = list(chunks.keys())[-1]
        edge = None
        borders_data.append([])
        border = borders_data[-1]

        pos_x, x, pos_z, z = 0, 0, 0, 0

        while len(border) < 2 or border[0] != [pos_x * 16 + x, pos_z * 16 + z]:
            pos_x = edge_chunks_dict[chunk][0]
            pos_z = edge_chunks_dict[chunk][1]

            new_chunk = None
            new_edge = None

            if edge is None:
                for i in range(4):
                    if edge_chunks_dict[chunk][i + 2] == 0:
                        edge = i
                        break

            next_edge = edge + 1
            if next_edge == 4:
                next_edge = 0
            previous_edge = edge - 1
            if previous_edge == -1:
                previous_edge = 3

            if edge_chunks_dict[chunk][next_edge + 2] == 0:
                # border goes right
                # print("Border goes right.")
                new_chunk = chunk
                new_edge = next_edge
            else:
                if edge == 0:
                    x = 1
                    z = 0
                elif edge == 1:
                    x = 0
                    z = 1
                elif edge == 2:
                    x = -1
                    z = 0
                elif edge == 3:
                    x = 0
                    z = -1

                if str([pos_x + x, pos_z + z]) in edge_chunks_dict and edge_chunks_dict[str([pos_x + x, pos_z + z])][edge + 2] == 0:
                    # border goes straight
                    # print("Border goes straight.")
                    new_chunk = str([pos_x + x, pos_z + z])
                    new_edge = edge
                else:
                    if edge == 0:
                        x = 1
                        z = -1
                    elif edge == 1:
                        x = 1
                        z = 1
                    elif edge == 2:
                        x = -1
                        z = 1
                    elif edge == 3:
                        x = -1
                        z = -1

                    if edge_chunks_dict[str([pos_x + x, pos_z + z])][previous_edge + 2] == 0:
                        # border goes left
                        # print("Border goes left.")
                        new_chunk = str([pos_x + x, pos_z + z])
                        new_edge = previous_edge

            if edge == 0:
                x = 16
                z = 0
            elif edge == 1:
                x = 16
                z = 16
            elif edge == 2:
                x = 0
                z = 16
            elif edge == 3:
                x = 0
                z = 0

            # shorten borders
            # if edge_chunks_dict[str(border[-2])][1][edge] == 0 and edge_chunks_dict[str(border[-1])][1][edge] == 0:
            #     border.pop()
            border.append([pos_x * 16 + x, pos_z * 16 + z])
            chunk_info = edge_chunks_dict[str([pos_x, pos_z])]
            chunk_info[6 + edge] = [len(borders_data) - 1, len(border) - 1]
            edge_chunks_dict.update({str([pos_x, pos_z]): chunk_info})

            chunks.pop(chunk, None)
            chunk = new_chunk
            edge = new_edge
        else:
            border[-1].append([pos_x, pos_z])

    print(f"Discovered {len(borders_data)} borders.")

    print(f"Generating borders took {datetime.datetime.now() - start}.\n")

    return edge_chunks_dict, borders_data


def generate_pockets(edge_chunks_data, borders_data):
    # Assuming pockets have a shorter border than their parents
    # Assuming pockets don't contain other pockets
    print(f"Identifying pockets.")
    start = datetime.datetime.now()

    pockets_data = {}

    i = 0
    while i < len(borders_data):
        print(f"Checking pocket status of border {i} with other borders.")
        pos_x, pos_z = borders_data[i][-1][2]
        chunk = str([pos_x, pos_z])

        intersected_borders = {}

        # TODO duplicate border?
        if i == 19:
            i += 1
            continue

        edge = None
        for j in range(4):
            if edge_chunks_data[chunk][6 + j][0] == i:
                edge = j
                break

        if edge == 0 or edge == 2:
            minimum = min_z
            maximum = max_z
            position = pos_z
        else:
            minimum = min_x
            maximum = max_x
            position = pos_x

        x, z = 0, 0
        while minimum <= position + x + z <= maximum:
            examined_chunk = None
            if str([pos_x + x, pos_z + z]) in edge_chunks_data:
                examined_chunk = edge_chunks_data[str([pos_x + x, pos_z + z])]

            # print(examined_chunk)
            if examined_chunk and examined_chunk[6 + edge][0] != i and examined_chunk[6 + edge][0] != -1:
                intersections = 0
                if examined_chunk[6 + edge][0] in intersected_borders:
                    intersections = intersected_borders[examined_chunk[6 + edge][0]]
                intersected_borders.update({examined_chunk[6 + edge][0]: intersections + 1})

            edge = edge + 2
            if edge == 4:
                edge = 0
            if edge == 5:
                edge = 1

            if examined_chunk and examined_chunk[6 + edge][0] != i and examined_chunk[6 + edge][0] != -1:
                intersections = 0
                if examined_chunk[6 + edge][0] in intersected_borders:
                    intersections = intersected_borders[examined_chunk[6 + edge][0]]
                intersected_borders.update({examined_chunk[6 + edge][0]: intersections + 1})

            if edge == 0 or edge == 2:
                z += 1
            else:
                x += 1

        print(f"Intersected with border {intersected_borders}.")
        for border in intersected_borders:
            if intersected_borders[border] % 2 == 1:
                print(f"Border {i} is a pocket of border {border}.\n")

                if type(borders_data[i]) != list or type(borders_data[border]) != list:
                    continue

                pockets_data.setdefault(border, []).append(borders_data[i])
                borders_data[i] = border

        i += 1

    for border in pockets_data.keys():
        pockets_data.setdefault(border, []).append(0)
        if type(borders_data[border]) is not int:
            borders_data[border].append(pockets_data[border])
    print(f"Identifying pockets took {datetime.datetime.now() - start}.\n")

    return borders_data


# TODO apply new border format (current code based on old code)
def shorten_borders(border_data):
    for border in border_data:
        def step(index, next_direction):
            if border[index][-1] == next_direction:
                to_be_removed.append(border[index])
            index += 1
            if index > len(border):
                return
            if index == len(border):
                next_direction = border[1][-1]
            else:
                next_direction = border[index][-1]
            step(index, next_direction)

        to_be_removed = []
        step(1, border[2][-1])

        for element in to_be_removed:
            border.remove(element)

    return border_data


def generate_markers(borders_data):
    # export as marker for BlueMap
    print(f"Exporting marker_sets_{world_name}_{world_dimension}.txt for BlueMap.")
    start = datetime.datetime.now()

    with open(f"{dbc_path}\\marker_sets_{world_name}_{world_dimension}.txt", 'w') as outfile:
        outfile.write(f'    {world_version.replace(".", "-")}-generated-chunks: {{\n'
                      f'        label: "Generated chunks in {world_version}"\n'
                      f'        toggleable: true\n'
                      f'        default-hidden: true\n'
                      f'        sorting: 0\n'
                      f'        markers: {{\n')
        for border in borders_data:
            if type(border) is not int:
                outfile.write(f'            border{borders_data.index(border)}: {{\n'
                              f'                type: "shape"\n'
                              f'                position: {{ x: {border[0][0]}, y: 64, z: {border[0][1]} }}\n'
                              f'                label: "Border {borders_data.index(border)}"\n'
                              f'                shape: [\n')
                for point in border:
                    if len(point) > 2:
                        break
                    outfile.write(f"                    {{ x: {point[0]}, z: {point[1]} }}\n")
                outfile.write('                ]\n'
                              '                shape-y: 64\n'
                              f'                detail: "Chunks generated in border {borders_data.index(border)}"\n'
                              '                depth-test: false\n'
                              '                holes: [\n')
                if type(border[-1][-1]) is int:
                    for subBorder in border[-1]:
                        if type(subBorder) is not int:
                            outfile.write('                    [\n')
                            for point in subBorder:
                                if type(point) is not int:
                                    outfile.write(f"                        {{ x: {point[0]}, z: {point[1]} }}\n")
                            outfile.write('                    ]\n')
                outfile.write('                ]\n'
                              '            }\n')
        outfile.write("        }\n"
                      "    }\n")

        print(f"Exporting markers took {datetime.datetime.now() - start}.\n")


def generate_plot(name, chunks_data):
    print(f"Generating plot of {name}.")
    start = datetime.datetime.now()

    if os.path.exists(f"{dbc_path}\\{name}_{world_name}_{world_dimension}.png"):
        print("Found existing data.")
        image_save = f"{dbc_path}\\{name}_{world_name}_{world_dimension}.png"
    else:
        # Don't plot chunks far away
        if size[0] <= -1000 or size[1] <= -1000 or size[0] >= 1000 or size[1] >= 1000:
            image_size = (2000, 2000)
            offset = (min_x + 1000, min_z + 1000)
        else:
            image_size = size
            offset = (0, 0)

        image = Image.new("RGB", image_size)

        for chunk in chunks_data:
            if -1000 <= chunks_data[chunk][0] < 1000 and -1000 <= chunks_data[chunk][1] < 1000:
                image.putpixel((chunks_data[chunk][0] - min_x + offset[0], chunks_data[chunk][1] - min_z + offset[1]), (255, 255, 255))

        image_save = f"{dbc_path}\\{name}_{world_name}_{world_dimension}.png"
        image.save(image_save)

    dpi = mpl.rcParams['figure.dpi']
    im_data = plt.imread(image_save)
    height, width, depth = im_data.shape

    # What size does the figure need to be in inches to fit the image?
    figsize = width / float(dpi), height / float(dpi)

    # Create a figure of the right size with one axes that takes up the full figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes((0, 0, 1, 1))

    # Hide spines, ticks, etc.
    ax.axis('off')

    # Display the image.
    ax.imshow(im_data, cmap='gray')

    plt.show()

    print(f"Plotting took {datetime.datetime.now() - start}.\n")


def read_chunks(path):
    chunk_data = {}
    with open(path, 'r') as readfile:
        for line in readfile.readlines():
            temp_list = list(line.rstrip().split(";"))
            if len(temp_list) <= 2:
                x = 0
                while x < 32:
                    z = 0
                    while z < 32:
                        chunk = [int(temp_list[0]) * 32 + x, int(temp_list[1]) * 32 + z]
                        chunk_data.update({str(chunk): chunk})
                        z += 1
                    x += 1
            elif len(temp_list) <= 4:
                chunk = [int(temp_list[2]), int(temp_list[3])]
                chunk_data.update({str(chunk): chunk})
            else:
                chunk = [int(temp_list[2]), int(temp_list[3]),
                         int(temp_list[4]), int(temp_list[5]), int(temp_list[6]), int(temp_list[7])]
                chunk_data.update({str([int(temp_list[2]), int(temp_list[3])]): chunk})

    return chunk_data


def write_chunks(path, chunks_data):
    with open(path, 'w') as outfile:
        for chunk in chunks_data:
            chunk = chunks_data[chunk]
            rx = int(math.floor((chunk[0] / 32)))
            rz = int(math.floor((chunk[1] / 32)))
            edge = ""
            if len(chunk) > 2:
                edge = f";{chunk[2]};{chunk[3]};{chunk[4]};{chunk[5]}"
            outfile.write(f'{rx};{rz};{chunk[0]};{chunk[1]}{edge}\n')


def discover_border_chunks():
    print(f"Welcome to Discover Border Chunks, running script version {version}.\n")
    start_everything = datetime.datetime.now()

    global root
    global world_version
    global world_name
    global world_dimension
    global dbc_path

    if root.endswith("\\"):
        root = root[:-1]

    if not folders_exists():
        print("Specified folder does not exist.")
        return

    dimensions = ["DIM0", "DIM-1", "DIM1"]
    dimensions_bukkit = ["", "_nether", "_the_end"]

    for world in range(len(world_versions)):
        for dimension in range(3):
            start = datetime.datetime.now()

            world_version = world_versions[world]
            world_name = world_names[world]
            world_dimension = dimensions[dimension]

            print(f"\nDiscovering border chunks in {world_version}, {world_dimension}.\n")

            dimension_appender = '\\' + dimensions[dimension] if dimension != 0 else ""
            region_path = (f"{root}\\{world_version}\\"
                           f"{world_name + (dimensions_bukkit[dimension] if not world_vanilla[world] else '')}"
                           f"{dimension_appender}\\region")
            dbc_path = f"{root}\\{world_version}\\discover-border-chunks"

            if not os.path.exists(dbc_path):
                os.makedirs(dbc_path)

            chunks = generate_chunks(region_path)

            edge_chunks = generate_edge_chunks(chunks)

            updated_edge_chunks, borders = generate_borders(edge_chunks)

            borders_pocketed = generate_pockets(updated_edge_chunks, borders)

            # borders_shortened = shorten_borders(borders_pocketed)

            generate_markers(borders_pocketed)

            print(f"Discovering border chunks in {world_version}, {world_dimension} took {datetime.datetime.now() - start}.\n")

    print(f"Everything took {datetime.datetime.now() - start_everything}.\n")


discover_border_chunks()
