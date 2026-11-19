// 🛰 Synthetic native-reference fixture. Keep alias prose and hidden trivia.
package ReferenceComposition {
    part def <S> 'Sénsor::unit';
    alias DetectorAlias for 'Sénsor::unit';
    alias <AS> SensorAlias for 'Sénsor::unit';
    alias DetectorChain for DetectorAlias;
    part direct : 'Sénsor::unit';
    part shortRef : S;
    part globalRef : $::ReferenceComposition::'Sénsor::unit';
    part aliasRef : DetectorAlias;
    part aliasShortRef : AS;
    part chained : DetectorChain;
    part def <O> Outer {
        part def <I> 'Inner::device';
        alias Remote for ReferenceComposition::'Sénsor::unit';
    }
    alias OuterAlias for Outer;
    alias OuterChain for OuterAlias;
    part qualified : OuterAlias::'Inner::device'; //* retain qualifier note */
    part shortPath : O::I;
    part chainPath : OuterChain::I;
    part remote : Outer::Remote;
    package Coincidence {
        alias 'Sénsor::unit' for ReferenceComposition::'Sénsor::unit';
        part aliasConsumer : 'Sénsor::unit';
    }
    part def Base { part <ROLE> role [2] : S; }
    part def Derived :> Base { part :>> ROLE : S; }
    part current : Base;
    doc cseViews /* CSE-VIEWS/1.1
    {"views":[{"id":"PC_REFERENCE","kind":"physical_composition","mode":"definitions","nodes":[
      {"id":"Outer","element":"ReferenceComposition::Outer","parent":null,"level":0,"edge":null},
      {"id":"Inner","element":"ReferenceComposition::Outer::'Inner::device'","parent":"Outer","level":1,"edge":"OwnInner"}
    ]},{"id":"PC_SENSOR","kind":"physical_composition","mode":"definitions","nodes":[
      {"id":"Sensor","element":"ReferenceComposition::'Sénsor::unit'","parent":null,"level":0,"edge":null}
    ]}]}
    */
}
