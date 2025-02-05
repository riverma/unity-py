from unity_sds_client.unity_exception import UnityException
from unity_sds_client.resources.collection import Collection, Dataset, DataFile
import datetime
import pytest
import os

@pytest.fixture
def cleanup_update_test():
    yield None
    print("Cleanup...")

def test_read_corrupt_stac():
    with pytest.raises(UnityException):
        Collection.from_stac("tests/test_files/doesnt.exist")
    with pytest.raises(UnityException):
        collection = Collection.from_stac("tests/test_files/catalog_corrupt_02.json")
    with pytest.raises(UnityException):
        collection = Collection.from_stac("tests/test_files/catalog_corrupt.json")

def test_read_stac():
    collection = Collection.from_stac("tests/test_files/cmr_granules.json")
    assert collection.collection_id == "C2011289787-GES_DISC"
    datasets = collection.datasets
    assert len(datasets) == 2

    # Added 8/10/23 to check the STAC collection information
    assert datasets[1].collection_id == 'C2011289787-GES_DISC'

    data_files = collection.data_locations()
    assert len(data_files) == 6
    data_files = collection.data_locations(["data","opendap"])
    assert len(data_files) == 4
    data_files = collection.data_locations(["data","opendap","metadata"])
    assert len(data_files) == 6
    data_files = collection.data_locations(["data"])
    assert len(data_files) == 2
    for x in data_files:
        assert x in ['https://data.gesdisc.earthdata.nasa.gov/data/CHIRP/SNDR13CHRP1.2/2016/235/SNDR.SS1330.CHIRP.20160822T0005.m06.g001.L1_AQ.std.v02_48.G.200425095850.nc', 'https://data.gesdisc.earthdata.nasa.gov/data/CHIRP/SNDR13CHRP1.2/2016/235/SNDR.SS1330.CHIRP.20160822T0011.m06.g002.L1_AQ.std.v02_48.G.200425095901.nc']

        #Try a "classic" catalog + item files stac catalog
    collection = Collection.from_stac("tests/test_files/catalog_01.json")
    datasets = collection.datasets
    # Added 8/10/23 to check the STAC collection information
    assert datasets[0].collection_id == 'collection_test'
    assert len(datasets) == 1
    data_files = collection.data_locations()
    assert len(data_files) == 2
    data_files = collection.data_locations(["data"])
    assert len(data_files) == 1
    data_files = collection.data_locations(["metadata_stac"])
    assert len(data_files) == 1
    assert data_files[0] == "/unity/ads/sounder_sips/chirp_test_data/SNDR.SS1330.CHIRP.20160829T2317.m06.g233.L1_AQ.std.v02_48.G.200425130422.json"


def test_write_stac():
    collection = Collection.from_stac("tests/test_files/cmr_granules.json")
    Collection.to_stac(collection, "tests/test_files/tmp" )

    collection = Collection.from_stac("tests/test_files/catalog_01.json")
    Collection.to_stac(collection, "tests/test_files/tmp" )



def test_unity_to_stac():
    root = os.getcwd()
    application_output_directory = root + "/tests/test_files/tmp2"
    assert os.path.isabs(application_output_directory) == True

    #Create a collection
    collection  = Collection("SNDR13CHRP1AQCal_rebin")

    # Create a Dataset for the collection
    dataset_name = "SNDR.SS1330.CHIRP.20230615T0131.m06.g001.L1_AQ_CAL.std.v02_54.G.200615152827"
    dataset_start_time = "2023-06-15T01:31:12.467113Z"
    dataset_end_time = "2023-06-15T01:36:12.467113Z"
    dataset_create_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    dataset = Dataset(dataset_name, collection.collection_id, dataset_start_time, dataset_end_time, dataset_create_time)

    #Add 2 files to the dataset
    dataset.add_data_file(DataFile("data","./file.nc"))
    dataset.add_data_file(DataFile("metadadata", "./file.xml"))
    assert len(dataset.datafiles) == 2


    # Add arbitrary metadata to the product
    dataset.add_property("percent_cloud_cover", .01)

    #Add the dataset to the collection
    collection.add_dataset(dataset)

    # Add another file...
    dataset_name = "SNDR.SS1330.CHIRP.20230615T0131.m06.g001.L1_AQ_CAL.std.v02_54.G.200615152827_01"
    dataset2 = Dataset(dataset_name, collection.collection_id, dataset_start_time, dataset_end_time, dataset_create_time)
    dataset2.add_data_file(DataFile("data",application_output_directory+"/file2.nc"))
    dataset2.add_data_file(DataFile("metadadata",application_output_directory + "/file2.xml"))
    collection.add_dataset(dataset2)

    assert len(dataset.datafiles) == 2
    assert len(dataset2.datafiles) == 2

    Collection.to_stac(collection, application_output_directory)


    # Read in the just written stac file to confirm paths are absolute
    collection = Collection.from_stac("tests/test_files/tmp2/catalog.json")
    assert len(collection._datasets) == 2
    prop_count = 0

    for d in collection._datasets:
        # Added 8/10/23 to check the STAC collection information
        assert d.collection_id == 'SNDR13CHRP1AQCal_rebin'
        for df in d.datafiles:
            assert application_output_directory in df.location
            assert os.path.isabs(df.location) == True


        if "percent_cloud_cover" in d.properties:
            prop_count +=1
    assert prop_count == 1
