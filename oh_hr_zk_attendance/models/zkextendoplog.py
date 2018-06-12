def zkextendoplog(self, index=0):
    try:
        test = self.extlogtrynumber
    except:
        self.extlogtrynumber = 1
        
    data_seq = [ self.data_recv.encode("hex")[4:6], self.data_recv.encode("hex")[6:8] ]
    #print data_seq
    
    if index==0:
        self.data_seq1 = hex( int( data_seq[0], 16 ) + int( '104', 16 ) ).lstrip("0x")
        self.data_seq2 = hex( int( data_seq[1], 16 ) + int( '19', 16 ) ).lstrip("0x")
        desc = ": +104, +19" 
        header="0b00"
    elif index==1:
        self.data_seq1 = hex( abs( int( data_seq[0], 16 ) - int( '2c', 16 ) ) ).lstrip("0x")
        self.data_seq2 = hex( abs( int( data_seq[1], 16 ) - int( '2', 16 ) ) ).lstrip("0x")
        desc = ": -2c, -2" 
        header="d107"
    elif index>=2:
        self.data_seq1 = hex( abs( int( data_seq[0], 16 ) - int( '2c', 16 ) ) ).lstrip("0x")
        self.data_seq2 = hex( abs( int( data_seq[1], 16 ) - int( '2', 16 ) ) ).lstrip("0x")
        desc = ": -2c, -2" 
        header="ffff"
    
    
    #print self.data_seq1+"  "+self.data_seq2
    if len(self.data_seq1) >= 3:
        self.data_seq2 = hex( int( self.data_seq2, 16 ) + int( self.data_seq1[:1], 16) ).lstrip("0x")
        self.data_seq1 = self.data_seq1[-2:]
        
    if len(self.data_seq2) >= 3:
        self.data_seq1 = hex( int( self.data_seq1, 16 ) + int( self.data_seq2[:1], 16) ).lstrip("0x")
        self.data_seq2 = self.data_seq2[-2:]
    
    if len(self.data_seq1) <= 1:
        self.data_seq1 = "0"+self.data_seq1
        
    if len(self.data_seq2) <= 1:
        self.data_seq2 = "0"+self.data_seq2
    
    
    counter = hex( self.counter ).lstrip("0x")
    if len(counter):
        counter = "0" + counter
        
    #print self.data_seq1+" "+self.data_seq2+desc   
    data = header+self.data_seq1+self.data_seq2+self.id_com+counter+"00457874656e644f504c6f6700"
    self.zkclient.sendto(data.decode("hex"), self.address)
    #print data
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
    except:
        bingung=1
        if self.extlogtrynumber == 1:
            self.extlogtrynumber = 2
            zkextendoplog(self)
    
    self.id_com = self.data_recv.encode("hex")[8:12]
    self.counter = self.counter+1
    #print self.data_recv.encode("hex")
    return self.data_recv[8:]
