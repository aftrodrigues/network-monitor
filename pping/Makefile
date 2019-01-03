# should only need to change LIBTINS to the libtins install prefix
# (typically /usr/local unless overridden when tins built)
LIBTINS = /home/andrei/Documents/python/monitor/libtins-master
CPPFLAGS += -I$(LIBTINS)/include
LDFLAGS += -L$(LIBTINS)/lib -ltins -lpcap
CXXFLAGS += -std=c++14 -g -O3 -Wall

pping:  pping.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -o pping pping.cpp $(LDFLAGS)

clean:
	rm pping
