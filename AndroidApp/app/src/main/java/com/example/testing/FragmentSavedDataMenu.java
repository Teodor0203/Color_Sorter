package com.example.testing;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.util.Log;
import android.util.TypedValue;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public class FragmentSavedDataMenu extends Fragment {

    private LinearLayout savedDataContainer;
    List<String> allDataSaved = new ArrayList<>();

    SaveDataManager saveDataManager = new SaveDataManager();

    public FragmentSavedDataMenu() {}

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_saved_data_menu, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        savedDataContainer = view.findViewById(R.id.trails_container);
        savedDataContainer.removeAllViews();

        List<String> loadedSavedData = loadSavedData(getContext());

        if(loadedSavedData != null)
        {
            for (String savedDataName : loadedSavedData) {
                addSavedDataButton(savedDataName);
            }
        }
    }

    private void addSavedDataButton(String fileName) {
        Button savedDataButton = new Button(getActivity());

        savedDataButton.setText(fileName);

        int widthInPx = (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                340,
                getResources().getDisplayMetrics()
        );

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                widthInPx,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );

        params.setMargins(0, 0, 0, 20);
        savedDataButton.setLayoutParams(params);

        savedDataButton.setHeight(200);
        savedDataButton.setTextSize(35);
        savedDataButton.setBackgroundColor(getResources().getColor(R.color.ViewColor, null));
        savedDataButton.getBackground().setAlpha(150);
        savedDataButton.setTextColor(getResources().getColor(R.color.white, null));
        savedDataButton.setBackgroundResource(R.drawable.button_radius);

        savedDataContainer.addView(savedDataButton);

        savedDataButton.setOnClickListener(view -> {
            getParentFragmentManager().beginTransaction()
                    .setCustomAnimations(
                    R.anim.fade_in,
                    R.anim.fade_out,
                    R.anim.fade_in,
                    R.anim.fade_out
            ).replace(R.id.rootContainer, new FragmentShowSavedData(fileName)).addToBackStack(null).commit();

        });

        savedDataButton.setOnLongClickListener(view -> {
            String[] options = {"Rename", "Delete"};
            AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
            builder.setTitle("Choose an action");
            builder.setItems(options, (dialog, which) -> {
                switch (which) {
                    case 0: // Rename
                        saveDataManager.showRenameDialog(getContext(), fileName, savedDataButton);
                        break;
                    case 1: // Delete
                        saveDataManager.deleteFile(getContext(), fileName, savedDataButton, savedDataContainer);
                        break;
                }
            });
            builder.show();
            return true;
        });

    }

    private void showRenameDialog(String oldName, Button buttonToUpdate) {
        AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
        builder.setTitle("Rename file");

        final EditText input = new EditText(getActivity());
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setText(oldName);

        builder.setView(input);

        builder.setPositiveButton("OK", (dialog, which) -> {
            String newName = input.getText().toString();
            if (!newName.trim().isEmpty()) {
                buttonToUpdate.setText(newName);
                // TODO: actualizează și în datele persistente, dacă folosești SharedPreferences sau fișiere
                Toast.makeText(getActivity(), "Renamed to " + newName, Toast.LENGTH_SHORT).show();
            }
        });

        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());

        builder.show();
    }
    private List<String> loadSavedData(Context context)
    {
        try
        {
            FileInputStream fis = context.openFileInput("data.txt");
            BufferedReader reader = new BufferedReader(new InputStreamReader(fis));

            reader.readLine();
            String line;
            line = reader.readLine();

            while(line != null)
            {
                if (!allDataSaved.contains(line))
                {
                    allDataSaved.add(line);
                }
                line = reader.readLine();
            }
            fis.close();
        }
        catch (Exception e)
        {
            Log.e("SavedDataMenu","Error loading index: " + e.getMessage(), e);
        }

       return allDataSaved;
    }
}