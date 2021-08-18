import helper_ned as hned

def main():
  filename = 'ned_tmp.txt'

  with open(filename, 'wt') as f:
    #hned.writeX2Connections(f, object_names = ["eNB", "microCell"], quantities= [7, 4*7])
    hned.writeSeparation(f, "X2 Connections")
    hned.writeComment(f, text= "Hotspot0")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [0])
    hned.writeComment(f, text= "Hotspot1")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [4])
    hned.writeComment(f, text= "Hotspot2")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [8])
    hned.writeComment(f, text= "Hotspot3")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [12])
    hned.writeComment(f, text= "Hotspot4")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [16])
    hned.writeComment(f, text= "Hotspot5")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [20])
    hned.writeComment(f, text= "Hotspot6")
    hned.writeX2Connections(f, object_names = ["microCell"], quantities= [4], initial_values= [24])

if __name__ == "__main__":
  main()
  print("Done")