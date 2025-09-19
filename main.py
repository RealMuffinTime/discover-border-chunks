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

min_pos, max_pos, size = (0, 0), (0, 0), (0, 0)
world_version, world_name, world_dimension, dbc_path = "", "", "", ""

version = "v0.3.0-pre"

# TODO MCA selects different
# TODO generate differences between worlds
# TODO improve generate pockets hashmap again? earlier in the process?
# TODO shorten borders, but pockets?
# TODO generate_isles
# TODO shortest distance on pocket check

# It is recommended to generate chunks data yourself using MCA Selector filters, you can use this one:
# Status = "minecraft:noise" OR Status = "minecraft:surface" OR Status = "minecraft:carvers" OR Status = "minecraft:liquid_carvers" OR Status = "minecraft:features" OR Status = "minecraft:light" OR Status = "minecraft:spawn" OR Status = "minecraft:heightmaps" OR Status = "minecraft:full" OR (Status = "minecraft:structure_starts" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:structure_references" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:biomes" AND Palette contains "minecraft:bedrock") OR (Status = "minecraft:empty" AND Palette contains "minecraft:bedrock")
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
                                "liquid_carvers" or state == "features" or state == "light" or state ==
                                "spawn" or state == "heightmaps" or state == "full"):
                            chunks_dict.update({str(position) : position})
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
                                            chunks_dict.update({str(position) : position})
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

    global max_pos
    max_pos = (
        max(chunks_data[key][0] for key in chunks_data.keys()),
        max(chunks_data[key][1] for key in chunks_data.keys()))
    print("Max Pos:", max_pos)

    global min_pos
    min_pos = (
        min(chunks_data[key][0] for key in chunks_data.keys()),
        min(chunks_data[key][1] for key in chunks_data.keys()))
    print("Min Pos:", min_pos)

    global size
    size = (abs(min_pos[0] - max_pos[0]) + 1, abs(min_pos[1] - max_pos[1]) + 1)
    print("Size:", size)
    print(f"Generating sizes took {datetime.datetime.now() - start}.\n")


def generate_edge_chunks(chunks_dict):
    print("Generating edge_chunks.")
    start = datetime.datetime.now()

    if os.path.exists(f"{dbc_path}\\edge_chunks_{world_name}_{world_dimension}.csv"):
        print("Found existing data.")
        edge_chunks_dict = read_chunks(f"{dbc_path}\\edge_chunks_{world_name}_{world_dimension}.csv")
    else:
        edge_chunks_dict = {}

        for key in chunks_dict.keys():
            pos_x = chunks_dict[key][0]
            pos_z = chunks_dict[key][1]

            # 0 border, 1 no border
            chunk_info = [0, 0, 0, 0]

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
                edge_chunks_dict.update({key : chunk})

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

        while len(border) < 2 or border[0] != (pos_x * 16 + x, pos_z * 16 + z):
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

            # TODO shorten borders, but pockets?
            # if edge_chunks_dict[str(border[-2])][1][edge] == 0 and edge_chunks_dict[str(border[-1])][1][edge] == 0:
            #     border.pop()
            border.append((pos_x * 16 + x, pos_z * 16 + z))

            chunks.pop(chunk, None)
            chunk = new_chunk
            edge = new_edge

    borders_data = sorted(borders_data, key=len, reverse=True)

    print(f"Discovered {len(borders_data)} borders.")

    print(f"Generating borders took {datetime.datetime.now() - start}.\n")

    return borders_data

# def shorten_borders():
#     for border in borders:
#         def step(index, next_direction):
#             if border[index][-1] == next_direction:
#                 to_be_removed.append(border[index])
#             index += 1
#             if index > len(border):
#                 return
#             if index == len(border):
#                 next_direction = border[1][-1]
#             else:
#                 next_direction = border[index][-1]
#             step(index, next_direction)
#
#         to_be_removed = []
#         step(1, border[2][-1])
#
#         for element in to_be_removed:
#             border.remove(element)
#
#     with open(f"{dbc_path}\\borders_{world_name}_{world_dimension}.txt", 'w') as outfile:
#         outfile.write('\n'.join(str(border) for border in borders))
#
# shorten_borders()

def generate_pockets(borders_data):
    # Assuming pockets have a shorter border than their parents
    # TODO improve!!!!
    print(f"Identifying pockets.")
    start = datetime.datetime.now()

    pockets = 0
    i = 1
    while i < len(borders_data):
        j = 1
        while j <= i:
            position = 0
            k = 0
            k_valid = -2
            counter = 0
            intersection = None

            skip = False
            while borders_data[i] is not None and borders_data[i - j] is not None and not skip and borders_data[i][position][0] + 16 * k <= (max_pos[0] + 1) * 16:
                if (borders_data[i][position][0] + 16 * k, borders_data[i][position][1]) in borders_data[i - j]:
                    if k - 1 == k_valid:
                        # intersection in same direction, not good
                        # change current position and reset other vars
                        position += 1
                        k = 0
                        k_valid = -2
                        counter = 0
                        intersection = None
                        if position >= len(borders_data[i]) - 1:
                            # could not determine if border is inside other border
                            print(f"Pocket identification failed for border {str(i)}.")
                            skip = True
                        continue
                    if intersection is None:
                        intersection = (borders_data[i][position][0] + 16 * k, borders_data[i][position][1])
                    k_valid = k
                    counter += 1
                k += 1
            if counter % 2 != 0:
                print(f"Pocketing border {str(i)} into border {str(i - j)}.")
                # not the shortest, but short enough
                # shorter_position = None
                # for position in borders_data[i]:
                #     distance = math.sqrt((position[0] - intersection[0]) ** 2 + (position[1] - intersection[1]) ** 2)
                #     if shorter_position is None or distance < math.sqrt((shorter_position[0] - intersection[0]) ** 2 + (shorter_position[1] - intersection[1]) ** 2):
                #         shorter_position = position
                # for position in borders_data[i - j]:
                #     distance = math.sqrt((position[0] - shorter_position[0]) ** 2 + (position[1] - shorter_position[1]) ** 2)
                #     if distance < math.sqrt((intersection[0] - shorter_position[0]) ** 2 + (intersection[1] - shorter_position[1]) ** 2):
                #         intersection = position

                intersection_index = borders_data[i - j].index(intersection)
                # borders_data[i].pop()
                # while borders_data[i][0] != shorter_position:
                #     temp_position = borders_data[i][0]
                #     borders_data[i].pop(0)
                #     borders_data[i].append(temp_position)
                # borders_data[i].append(shorter_position)
                for position in reversed(borders_data[i]):
                    borders_data[i - j].insert(intersection_index, position)
                borders_data[i - j].insert(intersection_index, intersection)
                borders_data[i] = None
                pockets += 1
            else:
                if i == 3:
                    print(counter)
                    print(f"Border {str(i)} not a pocket in border {str(i - j)}.")
            j += 1
        i += 1
    print(f"\nIdentified and integrated {pockets} pockets.")
    print(f"Identifying pockets took {datetime.datetime.now() - start}.\n")

    return borders_data


def generate_isles(borders_data):
    # TODO
    return borders_data


def generate_markers(borders_data):
    # export as marker for BlueMap
    print(f"Exporting marker_sets_{world_name}_{world_dimension}.txt for BlueMap.")
    start = datetime.datetime.now()

    with open(f"{dbc_path}\\marker_sets_{world_name}_{world_dimension}.txt", 'w') as outfile:
        outfile.write(f'marker-sets: {{\n'
                      f'    {world_version}-generated-chunks: {{\n'
                      f'        label: "Generated chunks in {world_version}"\n'
                      f'        toggleable: true\n'
                      f'        default-hidden: true\n'
                      f'        sorting: 0\n'
                      f'        markers: {{\n')
        for border in borders_data:
            if border is not None:
                outfile.write(f'            border{borders_data.index(border)}: {{\n'
                              f'                type: "shape"\n'
                              f'                position: {{ x: {border[0][0]}, y: 64, z: {border[0][1]} }}\n'
                              f'                label: "Border {borders_data.index(border)}"\n'
                              f'                shape: [\n')
                for point in border:
                    outfile.write(f"                    {{ x: {point[0]}, z: {point[1]} }}\n")
                outfile.write('                ]\n'
                              '                shape-y: 64\n'
                              f'                detail: "Chunks generated in border {borders_data.index(border)}"\n'
                              '                depth-test: false\n'
                              '            }\n')
        outfile.write("        }\n"
                      "    }\n"
                      "}\n")

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
            offset = (min_pos[0] + 1000, min_pos[1] + 1000)
        else:
            image_size = size
            offset = (0, 0)

        image = Image.new("RGB", image_size)

        for chunk in chunks_data:
            if -1000 <= chunks_data[chunk][0] < 1000 and -1000 <= chunks_data[chunk][1] < 1000:
                image.putpixel((chunks_data[chunk][0] - min_pos[0] + offset[0], chunks_data[chunk][1] - min_pos[1] + offset[1]), (255, 255, 255))

        image_save = f"{dbc_path}\\{name}_{world_name}_{world_dimension}.png"
        image.save(image_save)

    dpi = mpl.rcParams['figure.dpi']
    im_data = plt.imread(image_save)
    height, width, depth = im_data.shape

    # What size does the figure need to be in inches to fit the image?
    figsize = width / float(dpi), height / float(dpi)

    # Create a figure of the right size with one axes that takes up the full figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])

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
                        chunk_data.update({str(chunk) : chunk})
                        z += 1
                    x += 1
            elif len(temp_list) <= 4:
                chunk = [int(temp_list[2]), int(temp_list[3])]
                chunk_data.update({str(chunk) : chunk})
            else:
                chunk = [int(temp_list[2]), int(temp_list[3]),
                         int(temp_list[4]), int(temp_list[5]), int(temp_list[6]), int(temp_list[7])]
                chunk_data.update({str([int(temp_list[2]), int(temp_list[3])]) : chunk})

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

            borders = generate_borders(edge_chunks)

            borders_pocketed = generate_pockets(borders)

            borders_isled = generate_isles(borders_pocketed)

            generate_markers(borders)

            print(f"Discovering border chunks in {world_version}, {world_dimension} took {datetime.datetime.now() - start}.\n")

    print(f"Everything took {datetime.datetime.now() - start_everything}.\n")


discover_border_chunks()
