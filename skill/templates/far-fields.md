# Far fields

Fields an idea meeting deals to the personas in its four far seats (`METHOD.md`, step 2), two each, so the research
starts outside the user's life. The moderator draws them at random and never picks:

```sh
python3 -c "import random,sys;f=[l[2:].strip() for l in open('skill/templates/far-fields.md') if l.startswith('- ')];random.shuffle(f);print('\n'.join(f[:int(sys.argv[1])*2]))" 4
```

No field is dealt twice in a meeting, and none dealt in the last idea meeting is dealt again: check
the draw against the `far fields dealt` line of that meeting's round file, redraw any field that
repeats, and write this meeting's fields into its own round file.
Add a field when a meeting shows a gap; remove one only when it has come to sit close to the
user's own work. One field per line.

- container shipping and port work
- funeral homes and memorial services
- beekeeping and pollination services
- amateur sports refereeing
- home care for older people
- museum conservation and collections
- commercial fishing and fish auctions
- wedding and event planning
- long-haul trucking
- community theatre and small venues
- veterinary clinics
- school cafeterias and institutional catering
- second-hand clothing and textile recycling
- small-scale farming and farmers' markets
- amateur radio and weather watching
- public libraries
- construction site safety
- piano tuning and instrument repair
- court interpreting and sign language
- lost property and returns handling
- vending machines and laundromats
- seed banks and plant nurseries
- emergency dispatch
- cemeteries and genealogy
- hairdressing and barber shops
- scrap metal and demolition
- board game cafes and tabletop publishing
- driving schools
- tide pools, birdwatching and citizen science
- hospital wayfinding and patient transport
- choir and marching band organizing
- insurance claims adjusting
- locksmiths and security doors
- street food and night markets
- prison education and re-entry programs
- mountain rescue and trail maintenance
- dairy and cheese making
- auction houses and estate sales
- public transit scheduling
- children's birthday entertainment
- water utilities and plumbing
- bookbinding and small presses
- elevator maintenance
- dog training and kennels
- stage lighting and live sound
- pharmacy counters
- land surveying
- hospice volunteering
- competitive puzzle and quiz leagues
- shoe repair and tailoring
