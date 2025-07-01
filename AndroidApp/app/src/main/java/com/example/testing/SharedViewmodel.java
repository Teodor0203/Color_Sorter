package com.example.testing;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

public class SharedViewmodel extends ViewModel {

    private final String TAG = "SharedViewModel";
    private final MutableLiveData<Data> dataLiveData = new MutableLiveData<>();

    public LiveData<Data> getDataLiveData() {
        return dataLiveData;
    }

    public void setData(Data data) {
        dataLiveData.setValue(data);
    }

    public void updateColorID(int colorID) {
        Data curretnData = dataLiveData.getValue();

        if (curretnData == null) {
            curretnData = new Data(0);
        }

        curretnData.setColorID(colorID);
        dataLiveData.setValue(curretnData);
    }
}