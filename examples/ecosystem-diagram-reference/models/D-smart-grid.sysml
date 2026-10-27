package SmartGrid2010 {
 part def Domain { port comm; port electrical; }
 part DomainView {
  doc /* NIST SP1108 Fig3-1. View context and endpoint adapter ports are introduced; no organizational ownership claim. All connectors undirected. */
  part markets : Domain { doc /* Markets domain. */ }
  part operations : Domain { doc /* Operations domain. */ }
  part serviceProvider : Domain { doc /* Service Provider domain. */ }
  part bulkGeneration : Domain { doc /* Bulk Generation domain. */ }
  part transmission : Domain { doc /* Transmission domain. */ }
  part distribution : Domain { doc /* Distribution domain. */ }
  part customer : Domain { doc /* Customer domain. */ }
  connection DC01 connect markets.comm to operations.comm;
  connection DC02 connect markets.comm to serviceProvider.comm;
  connection DC03 connect operations.comm to serviceProvider.comm;
  connection DC04 connect markets.comm to bulkGeneration.comm;
  connection DC05 connect markets.comm to transmission.comm;
  connection DC06 connect markets.comm to distribution.comm;
  connection DC07 connect markets.comm to customer.comm;
  connection DC08 connect operations.comm to bulkGeneration.comm;
  connection DC09 connect operations.comm to transmission.comm;
  connection DC10 connect operations.comm to distribution.comm;
  connection DC11 connect operations.comm to customer.comm;
  connection DC12 connect serviceProvider.comm to customer.comm;
  connection DC13 connect bulkGeneration.comm to transmission.comm;
  connection DC14 connect transmission.comm to distribution.comm;
  connection DC15 connect distribution.comm to customer.comm;
  connection DE01 connect bulkGeneration.electrical to transmission.electrical;
  connection DE02 connect transmission.electrical to distribution.electrical;
  connection DE03 connect distribution.electrical to customer.electrical;
 }
}
